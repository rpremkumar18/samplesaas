"""Read-only GitHub access: downloads one repo tarball and reads text files in memory.

Nothing is ever extracted to disk, cloned or executed. Member names from the archive are only
used as labels (never as filesystem paths).
"""

import gzip
import io
import logging
import re
import tarfile
import time
import zlib
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote, urljoin, urlsplit

import httpx

from app.config import get_settings
from app.exceptions import ExternalServiceError, NotFoundError

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
ALLOWED_HOSTS = frozenset({"api.github.com", "codeload.github.com"})
MAX_REDIRECTS = 3
MAX_FILES = 40
MAX_FILE_BYTES = 60_000
MAX_TOTAL_CHARS = 120_000
MAX_CHARS_PER_FILE = 12_000
MAX_ARCHIVE_BYTES = 25 * 1024 * 1024  # compressed bytes downloaded
MAX_DECOMPRESSED_BYTES = 200 * 1024 * 1024  # bytes read out of the gzip stream
MAX_REPO_SIZE_KB = 200_000  # GitHub metadata "size" (includes history)
MAX_CANDIDATE_BYTES = 8 * 1024 * 1024  # text kept in memory while choosing files
MAX_MEMBERS = 20_000
REQUEST_TIMEOUT = 20.0
TOO_LARGE_MESSAGE = "This repository is too large to analyze."
MAX_LISTED_REPOS = 100
GITHUB_LOGIN_RE = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})")

SKIP_DIRS = frozenset(
    {"node_modules", "dist", "build", ".git", "venv", ".venv", "__pycache__", "vendor",
     "target", ".next", "coverage", ".idea", ".vscode", "out", "site-packages"}
)
SKIP_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp", ".pdf", ".zip", ".tar",
    ".gz", ".7z", ".rar", ".exe", ".dll", ".so", ".dylib", ".class", ".jar", ".pyc", ".woff",
    ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".mov", ".avi", ".wav", ".bin", ".o", ".a",
    ".min.js", ".map", ".csv", ".db", ".sqlite", ".lock", ".psd", ".ai",
)
SKIP_FILENAMES = frozenset(
    {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "pipfile.lock",
     "composer.lock", "cargo.lock", "gemfile.lock", "go.sum", "uv.lock", ".ds_store"}
)
SECRET_EXTENSIONS = (
    ".pem", ".key", ".p12", ".pfx", ".keystore", ".jks", ".ppk", ".gpg", ".kdbx", ".tfvars",
)
SECRET_NAME_PREFIXES = (
    ".env", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa", "credentials", "secrets.", "secret.",
    "terraform.tfstate", "service-account", "serviceaccount",
)
SECRET_FILENAMES = frozenset(
    {".npmrc", ".pypirc", ".netrc", ".htpasswd", ".git-credentials", "secrets", "credentials"}
)
PRIORITY_NAMES = frozenset(
    {"readme.md", "package.json", "requirements.txt", "pyproject.toml", "dockerfile",
     "docker-compose.yml", "main.py", "app.py", "index.js", "index.ts", "main.ts", "main.go"}
)
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


class PipelineTimeoutError(ExternalServiceError):
    """The overall analysis deadline was exceeded."""

    default_message = "The analysis took too long. Please try again."


class _TooLargeError(Exception):
    """Internal: a size cap was exceeded."""


@dataclass(frozen=True)
class PublicRepo:
    """Summary of a public repository for the repo picker."""

    name: str
    html_url: str
    description: str | None = None
    language: str | None = None
    pushed_at: str | None = None


@dataclass(frozen=True)
class RepoFile:
    """A text file fetched from a repository."""

    path: str
    content: str


@dataclass(frozen=True)
class RepoSnapshot:
    """Selected files plus a report of everything that was left out."""

    files: list[RepoFile]
    omitted_files: int = 0  # regular files in the repo that were not sent to the model
    truncated_files: int = 0  # sent, but cut to the per-file/total character cap
    secrets_excluded: int = 0  # never sent (also counted in omitted_files)
    file_cap_hit: bool = False
    scan_incomplete: bool = False  # archive scan stopped early (member/memory cap)

    @property
    def is_partial(self) -> bool:
        """True when the model is not seeing the whole repository."""
        return bool(self.omitted_files or self.truncated_files or self.scan_incomplete)


def _opt_str(value: object) -> str | None:
    """Return ``value`` when it is a string, else None."""
    return value if isinstance(value, str) else None


def is_secret_file(path: str) -> bool:
    """Return True for files likely to hold credentials, which must never reach the LLM."""
    name = path.rsplit("/", 1)[-1].lower()
    return (
        name in SECRET_FILENAMES
        or name.startswith(SECRET_NAME_PREFIXES)
        or name.endswith(SECRET_EXTENSIONS)
    )


def _should_skip(path: str, size: int) -> bool:
    """Return True for binaries, vendored/build output, lock files and oversized files."""
    parts = path.split("/")
    if any(part in SKIP_DIRS for part in parts[:-1]):
        return True
    name = parts[-1].lower()
    if name in SKIP_FILENAMES or name.endswith(SKIP_EXTENSIONS):
        return True
    return size <= 0 or size > MAX_FILE_BYTES


def _priority(path: str) -> tuple[int, int, str]:
    """Sort key: key files first, then shallow paths."""
    name = path.rsplit("/", 1)[-1].lower()
    return (0 if name in PRIORITY_NAMES else 1, path.count("/"), path)


def _clean_member_path(name: str) -> str | None:
    """Strip the top-level archive folder; return None for unsafe or empty names."""
    if "\\" in name or _CONTROL_RE.search(name):
        return None
    raw_parts = name.split("/")
    if name.startswith("/") or any(p in (".", "..") for p in raw_parts):
        return None
    parts = raw_parts[1:]  # drop "owner-repo-sha/"
    if not parts or any(p == "" for p in parts):
        return None
    return "/".join(parts)


def _is_rate_limited(response: httpx.Response, body: str = "") -> bool:
    """Detect GitHub primary/secondary rate limiting (not plain 403/404)."""
    if response.status_code == 429:
        return True
    if response.status_code != 403:
        return False
    return (
        response.headers.get("x-ratelimit-remaining") == "0"
        or "retry-after" in response.headers
        or "rate limit" in body.lower()
    )


class _Deadline:
    """Monotonic deadline shared by the fetch phase."""

    def __init__(self, deadline: float | None) -> None:
        self._deadline = deadline

    def remaining(self) -> float | None:
        """Seconds left, or None when unbounded."""
        return None if self._deadline is None else self._deadline - time.monotonic()

    def check(self) -> None:
        """Raise PipelineTimeoutError when time is up."""
        left = self.remaining()
        if left is not None and left <= 0:
            raise PipelineTimeoutError()

    def timeout(self) -> httpx.Timeout:
        """httpx timeout bounded by the remaining time."""
        self.check()
        left = self.remaining()
        limit = REQUEST_TIMEOUT if left is None else min(REQUEST_TIMEOUT, left)
        return httpx.Timeout(limit, connect=min(10.0, limit))


class _CompressedStream(io.RawIOBase):
    """File-like view over streamed response bytes enforcing the compressed-size cap."""

    def __init__(self, chunks: Iterator[bytes], limit: int, deadline: _Deadline) -> None:
        self._chunks = chunks
        self._limit = limit
        self._deadline = deadline
        self._buf = b""
        self.total = 0

    def readable(self) -> bool:
        """Mark as readable."""
        return True

    def readinto(self, b: Any) -> int:
        """Fill ``b`` from the network, aborting when the cap or deadline is exceeded."""
        if not self._buf:
            self._deadline.check()
            try:
                chunk = next(self._chunks)
            except StopIteration:
                return 0
            self.total += len(chunk)
            if self.total > self._limit:
                raise _TooLargeError()
            self._buf = chunk
        n = min(len(b), len(self._buf))
        b[:n] = self._buf[:n]
        self._buf = self._buf[n:]
        return n


class _CappedReader:
    """Wraps the gzip reader and caps total decompressed bytes."""

    def __init__(self, raw: Any, limit: int, deadline: _Deadline) -> None:
        self._raw = raw
        self._limit = limit
        self._deadline = deadline
        self.total = 0

    def read(self, size: int = -1) -> bytes:
        """Read at most ``size`` bytes; abort on bombs or timeouts."""
        self._deadline.check()
        data: bytes = self._raw.read(size if size > 0 else 65536)
        self.total += len(data)
        if self.total > self._limit:
            raise _TooLargeError()
        return data


class GitHubService:
    """Fetches a bounded set of text files from a public repo via one tarball download."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._token = get_settings().GITHUB_TOKEN
        # Redirects are followed manually so that hosts can be allow-listed.
        self._client = client or httpx.Client(base_url=GITHUB_API, follow_redirects=False)

    def _headers(self, url: str, accept: str) -> dict[str, str]:
        """Request headers; Authorization only goes to api.github.com."""
        headers = {
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept-Encoding": "identity",
        }
        host = urlsplit(url).hostname if url.startswith("http") else "api.github.com"
        if self._token and host == "api.github.com":
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        """Map non-success responses to distinct, user-safe errors."""
        status = response.status_code
        if status < 400:
            return
        body = ""
        if status == 403:
            try:
                body = response.text[:500]
            except (httpx.StreamError, UnicodeDecodeError):
                body = ""
        if _is_rate_limited(response, body):
            logger.warning(
                "GitHub rate limited (status %s, retry-after=%s)",
                status, response.headers.get("retry-after"),
            )
            raise ExternalServiceError(
                "GitHub rate limit reached. Please try again in a few minutes."
            )
        if status == 404:
            raise NotFoundError("Repository not found. Check the URL and that it is public.")
        if status in (401, 403):
            raise NotFoundError("This repository is not accessible. It must be public.")
        logger.warning("GitHub returned %s", status)
        raise ExternalServiceError("GitHub returned an unexpected error.")

    def _get_json(self, url: str, deadline: _Deadline) -> dict[str, Any]:
        """GET JSON from the API with uniform error mapping."""
        try:
            response = self._client.get(
                url,
                headers=self._headers(url, "application/vnd.github+json"),
                timeout=deadline.timeout(),
            )
        except httpx.HTTPError as exc:
            logger.warning("GitHub request failed: %s", type(exc).__name__)
            raise ExternalServiceError("Could not reach GitHub. Please try again later.") from exc
        self._raise_for_status(response)
        try:
            data = response.json()
        except ValueError as exc:
            raise ExternalServiceError("GitHub returned an unexpected error.") from exc
        return data if isinstance(data, dict) else {}

    def list_public_repos(self, login: str, limit: int = MAX_LISTED_REPOS) -> list[PublicRepo]:
        """Return a user's public, non-fork, non-archived repos, most recently pushed first."""
        if not GITHUB_LOGIN_RE.fullmatch(login):
            raise NotFoundError("GitHub username is invalid.")
        url = f"/users/{quote(login, safe='')}/repos"
        try:
            response = self._client.get(
                url,
                params={"type": "owner", "sort": "pushed", "per_page": 100},
                headers=self._headers(url, "application/vnd.github+json"),
                timeout=REQUEST_TIMEOUT,
            )
        except httpx.HTTPError as exc:
            logger.warning("GitHub request failed: %s", type(exc).__name__)
            raise ExternalServiceError("Could not reach GitHub. Please try again later.") from exc
        self._raise_for_status(response)
        try:
            data = response.json()
        except ValueError as exc:
            raise ExternalServiceError("GitHub returned an unexpected error.") from exc
        repos: list[PublicRepo] = []
        for item in data if isinstance(data, list) else []:
            if not isinstance(item, dict) or item.get("private") or item.get("fork"):
                continue
            if item.get("archived") or item.get("disabled"):
                continue
            name, html_url = item.get("name"), item.get("html_url")
            if not isinstance(name, str) or not isinstance(html_url, str):
                continue
            repos.append(
                PublicRepo(
                    name=name,
                    html_url=html_url,
                    description=_opt_str(item.get("description")),
                    language=_opt_str(item.get("language")),
                    pushed_at=_opt_str(item.get("pushed_at")),
                )
            )
        return repos[:limit]

    def fetch_repo_files(
        self, owner: str, repo: str, deadline: float | None = None
    ) -> RepoSnapshot:
        """Return a bounded snapshot of text files; ``deadline`` is a time.monotonic() value."""
        dl = _Deadline(deadline)
        base = f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
        meta = self._get_json(base, dl)
        if meta.get("private") is True:
            raise NotFoundError("This repository is private. The repository must be public.")
        raw_size = meta.get("size")
        size_kb = raw_size if isinstance(raw_size, int) else None
        if size_kb is not None and size_kb > MAX_REPO_SIZE_KB:
            raise ExternalServiceError(TOO_LARGE_MESSAGE)
        branch = str(meta.get("default_branch") or "main")
        tarball_url = f"{base}/tarball/{quote(branch, safe='/')}"
        return self._download_and_select(tarball_url, size_kb == 0, dl)

    def _download_and_select(self, url: str, maybe_empty: bool, dl: _Deadline) -> RepoSnapshot:
        """Stream the tarball (following allow-listed redirects) and pick files."""
        current = url
        try:
            for _ in range(MAX_REDIRECTS + 1):
                with self._client.stream(
                    "GET",
                    current,
                    headers=self._headers(current, "application/vnd.github+json"),
                    timeout=dl.timeout(),
                ) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        current = self._next_hop(current, response.headers.get("location"))
                        continue
                    if response.status_code == 409 or (
                        maybe_empty and response.status_code == 404
                    ):
                        raise NotFoundError("This repository is empty. Push some code first.")
                    if response.status_code >= 400:
                        response.read()
                        self._raise_for_status(response)
                    return self._read_archive(response, dl)
        except httpx.HTTPError as exc:
            logger.warning("GitHub download failed: %s", type(exc).__name__)
            raise ExternalServiceError("Could not reach GitHub. Please try again later.") from exc
        raise ExternalServiceError("GitHub returned too many redirects.")

    @staticmethod
    def _next_hop(current: str, location: str | None) -> str:
        """Resolve a redirect target, allowing only https GitHub hosts."""
        if not location:
            raise ExternalServiceError("GitHub returned an unexpected error.")
        base = current if current.startswith("http") else f"{GITHUB_API}{current}"
        target = urljoin(base, location)
        parts = urlsplit(target)
        if parts.scheme != "https" or (parts.hostname or "") not in ALLOWED_HOSTS:
            logger.warning("Rejected redirect to host %s", parts.hostname)
            raise ExternalServiceError("GitHub returned an unexpected redirect.")
        return target

    def _read_archive(self, response: httpx.Response, dl: _Deadline) -> RepoSnapshot:
        """Read tar members from the streamed gzip body, strictly in memory."""
        declared = response.headers.get("content-length")
        if declared and declared.isdigit() and int(declared) > MAX_ARCHIVE_BYTES:
            raise ExternalServiceError(TOO_LARGE_MESSAGE)
        raw = _CompressedStream(response.iter_bytes(65536), MAX_ARCHIVE_BYTES, dl)
        try:
            gz = gzip.GzipFile(fileobj=io.BufferedReader(raw))
            return self._select(_CappedReader(gz, MAX_DECOMPRESSED_BYTES, dl))
        except _TooLargeError as exc:
            raise ExternalServiceError(TOO_LARGE_MESSAGE) from exc
        except (tarfile.TarError, gzip.BadGzipFile, EOFError, zlib.error, OSError) as exc:
            logger.warning("Unreadable repository archive: %s", type(exc).__name__)
            raise ExternalServiceError("Could not read the repository archive.") from exc

    @staticmethod
    def _select(stream: _CappedReader) -> RepoSnapshot:
        """Walk tar members and choose which files to send."""
        candidates: dict[str, str] = {}
        candidate_bytes = 0
        omitted = 0
        secrets = 0
        scan_incomplete = False
        seen = 0
        with tarfile.open(fileobj=stream, mode="r|") as tar:  # type: ignore[call-overload]
            for member in tar:
                seen += 1
                if seen > MAX_MEMBERS:
                    scan_incomplete = True
                    break
                if not member.isreg():  # symlinks, hardlinks, devices, dirs
                    continue
                path = _clean_member_path(member.name)
                if path is None:
                    omitted += 1
                    continue
                if is_secret_file(path):
                    secrets += 1
                    omitted += 1
                    continue
                if _should_skip(path, member.size):
                    omitted += 1
                    continue
                if candidate_bytes + member.size > MAX_CANDIDATE_BYTES:
                    omitted += 1
                    scan_incomplete = True
                    continue
                fobj = tar.extractfile(member)
                data = fobj.read(MAX_FILE_BYTES + 1) if fobj is not None else b""
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    omitted += 1
                    continue
                if "\x00" in text or not text.strip():
                    omitted += 1
                    continue
                candidates[path] = text
                candidate_bytes += len(data)

        ordered = sorted(candidates, key=_priority)
        files: list[RepoFile] = []
        total = 0
        truncated = 0
        file_cap_hit = False
        for path in ordered:
            if len(files) >= MAX_FILES or total >= MAX_TOTAL_CHARS:
                file_cap_hit = True
                break
            text = candidates[path]
            kept = text[: min(MAX_CHARS_PER_FILE, MAX_TOTAL_CHARS - total)]
            if len(kept) < len(text):
                truncated += 1
            files.append(RepoFile(path=path, content=kept))
            total += len(kept)
        if not files:
            raise NotFoundError("No readable source files found in this repository.")
        omitted += len(ordered) - len(files)
        return RepoSnapshot(
            files=files,
            omitted_files=omitted,
            truncated_files=truncated,
            secrets_excluded=secrets,
            file_cap_hit=file_cap_hit,
            scan_incomplete=scan_incomplete,
        )

    def close(self) -> None:
        """Release the HTTP client."""
        self._client.close()
