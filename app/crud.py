"""Database operations. Route handlers stay thin by delegating here."""

from collections import Counter
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import Settings
from app.models import Click, Link
from app.schemas import ClickOut, DayCount, LinkStats
from app.shortcode import generate_code, validate_alias

_MAX_CODE_ATTEMPTS = 5


class CodeConflict(Exception):
    """The requested alias is already taken."""


class CodeExhausted(Exception):
    """Could not find a free random code after several attempts."""


async def get_link_by_code(session: AsyncSession, code: str) -> Link | None:
    return await session.scalar(select(Link).where(Link.code == code))


async def _code_taken(session: AsyncSession, code: str) -> bool:
    return await session.scalar(select(Link.id).where(Link.code == code)) is not None


async def create_link(
    session: AsyncSession,
    *,
    target_url: str,
    alias: str | None,
    expires_at: datetime | None,
    settings: Settings,
) -> Link:
    if alias is not None:
        code = validate_alias(alias)  # raises InvalidAlias
        if await _code_taken(session, code):
            raise CodeConflict(code)
        is_custom = True
    else:
        for _ in range(_MAX_CODE_ATTEMPTS):
            candidate = generate_code(settings.short_code_length)
            if not await _code_taken(session, candidate):
                code = candidate
                break
        else:
            raise CodeExhausted
        is_custom = False

    link = Link(code=code, target_url=target_url, expires_at=expires_at, is_custom=is_custom)
    session.add(link)
    await session.commit()
    await session.refresh(link)
    return link


async def record_click(
    sessionmaker: async_sessionmaker[AsyncSession],
    *,
    link_id: int,
    referrer: str | None,
    user_agent: str | None,
    ip_hash: str | None,
) -> None:
    """Runs as a background task after the redirect response is sent."""
    async with sessionmaker() as session:
        session.add(
            Click(
                link_id=link_id,
                referrer=referrer,
                user_agent=user_agent,
                ip_hash=ip_hash,
            )
        )
        link = await session.get(Link, link_id)
        if link is not None:
            link.click_count += 1
        await session.commit()


async def get_stats(session: AsyncSession, link: Link, *, recent_limit: int = 20) -> LinkStats:
    clicks = list(
        await session.scalars(
            select(Click).where(Click.link_id == link.id).order_by(Click.ts.desc())
        )
    )
    by_day = Counter(c.ts.date().isoformat() for c in clicks)
    return LinkStats(
        code=link.code,
        target_url=link.target_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
        total_clicks=link.click_count,
        clicks_by_day=[DayCount(day=day, count=n) for day, n in sorted(by_day.items())],
        recent_clicks=[
            ClickOut(ts=c.ts, referrer=c.referrer, user_agent=c.user_agent)
            for c in clicks[:recent_limit]
        ],
    )
