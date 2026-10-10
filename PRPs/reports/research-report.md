# Research Report - Assignment Roaster (2026-10-10)

Scope: read-only review of backend/app/services/{github_service,roast_service,submission_service}.py, routers/submissions.py, database.py, config.py, requirements.txt, frontend/package.json. Docs fetched live: GitHub REST docs (trees, rate limits) and Anthropic models overview + structured-outputs pages (platform.claude.com). Items marked "unconfirmed" were not verified live (from memory or not checked).

## 1. GitHub REST API

**Findings**
- Rate limits: unauthenticated 60 req/h per IP; authenticated 5,000 req/h. Secondary limits: 100 concurrent requests, 900 points/min REST. Exceeding returns 403 or 429 with `x-ratelimit-remaining` / `x-ratelimit-reset` headers.
- The service makes 1 (repo) + 1 (tree) + up to 40 (contents) = up to 42 requests per submission, sequentially. Unauthenticated, 60/h allows about 1 roast per hour per server IP. A `GITHUB_TOKEN` is effectively mandatory in production.
- Tree API: recursive tree is limited to 100,000 entries / 7 MB; when `truncated: true`, sub-trees should be fetched individually. The code never reads `truncated`, so huge repos are silently analysed from a partial file list.
- Empty repo: repo GET returns 200; the tree call returns 409 "Git Repository is empty" (unconfirmed live, commonly observed). `_get_json` maps every other >=400 to a generic "unexpected error", so the learner gets an unhelpful message.
- Default branch: correctly read from `default_branch` (fallback "main"). Good.
- Forks/archived: read normally via the API; payload has `fork` and `archived` flags, unused by the code. An unchanged fork would be roasted as the learner's work.
- Status mapping: 403 is mapped to "not found or private". Secondary-limit 403s (with `retry-after`, no `x-ratelimit-remaining: 0`) would be misreported as not found. Primary-limit cases are handled via the remaining=0 header check.
- Contents with `application/vnd.github.raw+json` returns raw bytes; files are pre-filtered by tree `size` (<=60 KB). Submodules (type `commit`) are skipped by the blob filter; symlink blobs hold a path string (harmless).
- Per-file fetch failures (including transient 5xx) are silently skipped, no retry.
- Filtering is sensible (dirs, binaries, lockfiles). Not excluded: `.env*`, `*.pem`/`*.key` (secrets would be sent to the LLM), `.ipynb` (noisy JSON).

**Evidence**: https://docs.github.com/en/rest/git/trees ; https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api ; github_service.py lines 84-129.

**Recommended**
- Must: Require/document `GITHUB_TOKEN` in deployment; on rate limit, include reset time in the message.
- Must: Handle the empty-repo 409 with a friendly "repository is empty" error.
- Should: Check `tree["truncated"]`; log it and note "large repo, partial review", or fetch sub-trees.
- Should: Treat 403 with `retry-after` or "rate limit"/"abuse" text as rate-limited, not not-found.
- Should: Cut requests: single tarball download (`GET /repos/{o}/{r}/tarball/{ref}`, extract in memory with size caps), or retry 5xx per file.
- Could: Skip `.env*`, keys, `.ipynb`; warn on forks/archived.

## 2. Anthropic API

**Findings**
- Model id: `claude-sonnet-5-5` is confirmed as the current Claude Sonnet 5.5 API id (pinned snapshot; alias identical), 1M context, 128K max output, $2/$10 per MTok, retirement not sooner than 2027-09-28. The defaults in config.py and roast_service.py are valid.
- JSON reliability: prompt-only JSON + Pydantic + one retry works but is the weaker option. Docs describe Structured Outputs: `output_config={"format": {"type": "json_schema", "schema": ...}}` or the SDK helper `client.messages.parse(..., output_format=PydanticModel)` returning `response.parsed_output`. Caveats from the docs: no `minimum/maximum/minLength` constraints (so score 0-100 and "at least 3 tips" must still be validated by Pydantic; `minItems` only 0 or 1), `stop_reason: "refusal"` and `max_tokens` truncation can still produce non-conforming output, first request per schema has grammar-compile latency. The fetched page's model-support list looked garbled; confirm Sonnet 5.5 support via the Models API `capabilities` (unconfirmed).
- Current code strips ``` fences, `json.loads`, `LLMRoast.model_validate`. The retry resends the identical prompt, and `stop_reason` is never checked, so a `max_tokens` cut-off burns a retry that will likely fail the same way.
- max_tokens 4096: adequate for roast + tips. Sonnet 5.5 uses adaptive thinking (default effort `high`); whether thinking tokens consume `max_tokens` for this model is unconfirmed - consider setting a lower `effort` and a larger `max_tokens` headroom.
- SDK client: created per call with defaults. Python SDK defaults (from SDK knowledge, unconfirmed this session): 10-minute timeout, 2 automatic retries with backoff on connection errors, 408/409/429/>=500 (so 429 and 529 overloaded are already retried). Code catches `anthropic.APIError` and returns one generic message; the learner cannot tell "busy" from "misconfigured".
- Sync client in a BackgroundTask: appropriate. `run_analysis` is a plain `def`, so Starlette runs it in the threadpool and the event loop is not blocked. Caveat: the default AnyIO threadpool is 40 threads shared with sync endpoints; each roast holds a thread for up to minutes.
- Cost: up to ~120k chars (~35k tokens) in x $2/MTok = ~$0.07, plus ~3k out ($0.03) => roughly $0.10 per roast. Caching not useful; Batch API not suitable for interactive UX.

**Evidence**: https://platform.claude.com/docs/en/about-claude/models/overview ; https://platform.claude.com/docs/en/build-with-claude/structured-outputs ; roast_service.py lines 57-95.

**Recommended**
- Must: Check `message.stop_reason` (`max_tokens`, `refusal`) and map to specific errors rather than blind retry.
- Should: Use `client.messages.parse(output_format=LLMRoast)` / `output_config` json_schema; keep Pydantic range validation and one retry.
- Should: Single module-level client with explicit `timeout` (e.g. 120 s) and `max_retries`; map `RateLimitError` / 529 to "AI is busy, retry shortly".
- Should: Log `usage.input_tokens/output_tokens` per roast.
- Could: Trial `claude-haiku-5-5` for cost; raise anthropic floor in requirements.

## 3. Thanglish prompt review

**Findings**
- Good: untrusted-data delimiters with tag-name escaping in content, "roast the code, never the person", no abuse/discrimination, do not repeat secrets, roast_text Thanglish vs English summary/tips.
- Gaps: no intensity control (beginners are the audience); no explicit ban on Tamil slang insults, family/caste/gender/region jokes; no length limits; "Thanglish" not pinned to Latin script (model may emit Tamil script); no score rubric (inconsistent scores); `file_path` not constrained to provided paths; no max tips; no guidance for tiny/trivial repos or truncated files; `path` attribute and `assignment_title` interpolated unescaped (low-risk injection vector).

**Recommended prompt changes**
1. Should - Tone/safety: "Tone: friendly teasing like a college senior, medium intensity. Never mock intelligence, family, gender, caste, religion, region or appearance; no profanity or slurs (including Tamil slang insults). End roast_text with one encouraging line. roast_text 80-150 words, Latin script only (no Tamil script)."
2. Should - Few-shot style anchor (have a native speaker vet it): "Machan, main.py-la 400 line oru function-ke irukku! Idhu function illa, oru serial maari mudiyave mudiyadhu. Variable names a, b, x1 - paathavangale 'enna da idhu?' nu kekkuvaanga. Aana logic correct-a work aaguthu, adhu super. Konjam split pannunga, bright future irukku!"
3. Should - Rubric and constraints: "Score: structure 25, correctness 25, readability 20, security 15, best practices 15, based only on provided files; if code is trivial or files were truncated/omitted, say so and score conservatively. file_path must be one of the provided paths or null. 3-8 tips, each description <= 60 words."
- Could: wrap title in a delimited tag and escape quotes in `path`.

## 4. FastAPI / SQLAlchemy practices

**Findings**
- Every handler in routers/submissions.py is `async def` but calls sync SQLAlchemy Session code and uses a sync `get_db` generator. Queries inside `async def` run on the event loop and block all requests while they execute. Options: (a) plain `def` handlers (FastAPI runs them, and sync dependencies, in the threadpool) - simplest; (b) `run_in_threadpool`; (c) full async SQLAlchemy - larger change. CLAUDE.md says "async endpoints", so document the deliberate exception. `get_current_user` was not reviewed; apply the same rule.
- BackgroundTasks run in-process after the response: lost on restart/crash, no retry, no concurrency cap, not shared across workers. OK for MVP with recovery; use ARQ/RQ/Celery or a Postgres-polled job table for production.
- Stuck jobs: a submission left in `pending/fetching/analyzing` after a crash is never recovered, and `reset_for_retry` only accepts `failed`, so the user can only delete it. Retry's status check/set is not atomic (double click can enqueue two tasks).
- Positives: background task uses its own session and closes it; failures are recorded with sanitized messages; `pool_pre_ping` on.
- If `_set_status` itself throws inside an `except` block, the outer catch-all logs and the row stays in its prior state.

**Evidence**: routers/submissions.py; database.py; submission_service.py lines 98-115; FastAPI docs https://fastapi.tiangolo.com/async/ and https://fastapi.tiangolo.com/tutorial/background-tasks/ (not re-fetched this session).

**Recommended**
- Must: Convert DB-touching handlers to `def` (or wrap in threadpool).
- Must: Stale-job sweep (startup + periodic): rows in pending/fetching/analyzing older than ~10 min become `failed` ("timed out, please retry"); allow retry of stale in-progress rows (verify an `updated_at` column exists).
- Should: Atomic retry (`UPDATE ... WHERE status='failed' RETURNING`) and no duplicate in-flight analyses.
- Should: Cap concurrent roasts (semaphore) and run a single worker, or move to a queue before scaling.
- Could: Adopt a job queue later.

## 5. Dependency advisories

Versions installed are unknown and no installers/audits were run (read-only); advisory IDs below are from memory - verify with `pip-audit` / `npm audit` / https://github.com/advisories (unconfirmed live).
- requirements.txt: every package uses only a lower bound except sqlalchemy (`>=2.0,<2.1`, consistent with the psycopg2 driver). No lockfile => non-reproducible builds, surprise major bumps (pydantic, fastapi, anthropic, bcrypt, httpx, pytest-asyncio).
- `python-multipart>=0.0.9`: older releases have DoS advisories (e.g. CVE-2024-53981, fixed 0.0.18). Raise floor to >=0.0.18.
- `anthropic>=0.40`: too old for `messages.parse` / `output_config` / Sonnet 5.5; raise the floor to the tested version.
- `bcrypt>=4.1`: bcrypt 5.x raises on passwords >72 bytes - validate/limit password length. `pyjwt>=2.8` fine; ensure `algorithms=[...]` is passed on decode.
- `psycopg2-binary`: upstream advises building `psycopg2` from source for production. `slowapi`: lightly maintained; `get_remote_address` rate-limits the proxy IP unless proxy headers are configured.
- `fastapi>=0.115`, `uvicorn>=0.30`: raise floors to tested versions (Starlette multipart DoS CVE-2024-47874 fixed in newer releases).
- frontend/package.json: version numbers are very high (typescript ^6.0.3, vitest ^4.1.11, vite ^6.4.4, framer-motion ^14.1.0, @chakra-ui/react ^3.37.0, react-router-dom ^7.18.4, axios ^1.20.0); could not verify they exist/are latest. Confirm a committed `package-lock.json`. Older vite (CVE-2025-30208 etc.) and axios (CVE-2025-27152, CVE-2025-58754) lines had advisories; ensure resolved versions are patched. Chakra UI v3 does not require framer-motion; drop it if unused.

**Recommended**
- Must: Run `pip-audit` and `npm audit` (in a temp copy/CI); commit lockfiles.
- Should: Use `~=` or upper-bounded majors; raise floors (python-multipart, anthropic, fastapi).
- Should: Enable Dependabot/Renovate.
- Could: Remove unused `framer-motion`.

## 6. Missing edge cases / MVP features

**Findings**
- Duplicate submissions: same repo can be resubmitted repeatedly (only 20/day/user cap); each costs ~$0.10 and ~42 GitHub calls. No dedupe by (user, repo, commit SHA); no commit SHA stored.
- No-code repos: zero readable files raises a clear error; README-only repos pass and are roasted as code; notebooks are fetched as raw JSON.
- Large/non-English: files >60 KB skipped, others truncated to 12k chars silently - the model is not told, so it may criticise "incomplete" code. UTF-16/Latin-1 files are treated as binary. Non-English comments are passed through without prompt guidance.
- Token cost: input bounded (~120k chars) but no pre-flight estimate, no global spend cap; only a per-user daily limit and per-IP slowapi.
- Privacy: public repo code (and any committed secrets) is sent to Anthropic; no learner-facing disclosure found in reviewed backend code (frontend not reviewed).
- Ownership: any user can submit any public repo (including someone else's or an unchanged fork); the roast replaces the previous one on re-run (no history).

**Recommended**
- Must: Privacy notice + consent before submit ("code from your public repo is sent to Anthropic's Claude API; do not submit repos containing secrets").
- Should: Dedupe/return existing completed roast for same user+repo (+HEAD SHA) within 24 h; store `commit_sha`.
- Should: Give the model a manifest of included/omitted/truncated files; skip `.env*`/keys.
- Should: Global daily roast/spend cap env var and token-usage logging.
- Could: Fork/unchanged-from-upstream warning; extract code cells from `.ipynb`; detect UTF-16; optional GitHub OAuth ownership check.

## Top-5 Recommendations
1. (Must) Convert sync-DB `async def` handlers to `def` (or threadpool) so queries stop blocking the event loop.
2. (Must) Add stuck-job recovery plus atomic retry (sweep stale in-progress rows to `failed`; allow retry of stale rows).
3. (Must) Harden GitHub fetching: require `GITHUB_TOKEN`, handle empty-repo 409, `truncated: true`, secondary-limit 403s; cut request count (tarball).
4. (Should) Use structured outputs (`messages.parse`) with `stop_reason` checks, explicit client timeout/retries, usage logging; keep Pydantic range validation.
5. (Must/Should) Add privacy disclosure and duplicate-submission dedupe; upgrade the prompt (tone/safety list, few-shot sample, scoring rubric); run `pip-audit`/`npm audit`, add lockfiles and raise dependency floors.
