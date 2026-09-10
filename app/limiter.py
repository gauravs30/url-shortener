"""Shared slowapi limiter. In-memory (per-process) for Phase 1 — see decisions/0005.
Phase 3 swaps the storage backend for Redis so limits hold across replicas."""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
