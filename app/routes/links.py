"""JSON API for creating and inspecting short links."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Request, status

from app.config import get_settings
from app.crud import CodeConflict, CodeExhausted, create_link, get_link_by_code, get_stats
from app.database import SessionDep
from app.limiter import limiter
from app.models import utcnow
from app.schemas import LinkCreate, LinkOut, LinkStats
from app.shortcode import InvalidAlias

router = APIRouter(prefix="/api", tags=["links"])

CodePath = Annotated[str, Path(pattern=r"^[A-Za-z0-9_-]{1,32}$")]


def _to_out(code: str, target_url: str, created_at, expires_at) -> LinkOut:
    base = get_settings().base_url.rstrip("/")
    return LinkOut(
        code=code,
        short_url=f"{base}/{code}",
        target_url=target_url,
        created_at=created_at,
        expires_at=expires_at,
    )


@router.post("/links", status_code=status.HTTP_201_CREATED)
@limiter.limit(get_settings().rate_limit)
async def create_short_link(request: Request, payload: LinkCreate, session: SessionDep) -> LinkOut:
    expires_at = payload.expires_at
    if payload.ttl_days is not None:
        expires_at = utcnow() + timedelta(days=payload.ttl_days)

    try:
        link = await create_link(
            session,
            target_url=payload.url,
            alias=payload.alias,
            expires_at=expires_at,
            settings=get_settings(),
        )
    except InvalidAlias as exc:
        raise HTTPException(422, str(exc)) from exc
    except CodeConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, f"alias '{exc}' is taken") from exc
    except CodeExhausted as exc:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE, "could not allocate a short code"
        ) from exc

    return _to_out(link.code, link.target_url, link.created_at, link.expires_at)


@router.get("/links/{code}")
async def get_link(code: CodePath, session: SessionDep) -> LinkOut:
    link = await get_link_by_code(session, code)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such link")
    return _to_out(link.code, link.target_url, link.created_at, link.expires_at)


@router.get("/links/{code}/stats")
async def get_link_stats(code: CodePath, session: SessionDep) -> LinkStats:
    link = await get_link_by_code(session, code)
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "no such link")
    return await get_stats(session, link)
