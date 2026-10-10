"""Shared slowapi limiter (separate module to avoid circular imports).

Storage is in-memory and per process: with N uvicorn workers/replicas the effective
limit is N times the configured one. Use Redis storage (``storage_uri``) if scaled out.
The client key is the remote address; behind nginx, uvicorn's ``--proxy-headers``
rewrites it from ``X-Forwarded-For`` so the real client IP is used.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
