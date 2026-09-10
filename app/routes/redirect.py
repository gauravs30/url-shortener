"""The public redirect endpoint: GET /{code}.

Registered last in main.py so it never shadows /api, /healthz, /static or /.
"""

import hashlib
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Request, status
from fastapi.responses import RedirectResponse
from starlette.background import BackgroundTask

from app.config import get_settings
from app.crud import get_link_by_code, record_click
from app.database import SessionDep, get_sessionmaker
from app.models import utcnow

router = APIRouter(tags=["redirect"])

CodePath = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{1,32}$")]


def _client_ip(request: Request) -> str | None:
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else None


def _hash_ip(ip: str | None) -> str | None:
    if not ip:
        return None
    salt = get_settings().ip_hash_salt
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()


@router.get("/{code}")
async def follow(code: CodePath, request: Request, session: SessionDep) -> RedirectResponse:
    link = await get_link_by_code(session, code)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such link")
    if link.is_expired(utcnow()):
        raise HTTPException(status.HTTP_410_GONE, "this link has expired")

    task = BackgroundTask(
        record_click,
        get_sessionmaker(),
        link_id=link.id,
        referrer=request.headers.get("referer"),
        user_agent=request.headers.get("user-agent"),
        ip_hash=_hash_ip(_client_ip(request)),
    )
    # 307 (not 301): keeps browsers from caching the hop, so analytics and
    # expiry keep working. See decisions/0004.
    return RedirectResponse(
        link.target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT, background=task
    )
