"""ORM models. Kept backend-agnostic (no PostgreSQL-only types) so the same
models run against SQLite in the test suite and PostgreSQL in Docker/prod."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    target_url: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    is_custom: Mapped[bool] = mapped_column(default=False)
    click_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")

    clicks: Mapped[list["Click"]] = relationship(
        back_populates="link", cascade="all, delete-orphan", passive_deletes=True
    )

    def is_expired(self, now: datetime | None = None) -> bool:
        if self.expires_at is None:
            return False
        exp = self.expires_at
        if exp.tzinfo is None:  # SQLite round-trips datetimes as naive
            exp = exp.replace(tzinfo=UTC)
        return (now or utcnow()) >= exp


class Click(Base):
    __tablename__ = "clicks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    link_id: Mapped[int] = mapped_column(ForeignKey("links.id", ondelete="CASCADE"), index=True)
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    referrer: Mapped[str | None] = mapped_column(Text, default=None)
    user_agent: Mapped[str | None] = mapped_column(Text, default=None)
    ip_hash: Mapped[str | None] = mapped_column(String(64), default=None)

    link: Mapped[Link] = relationship(back_populates="clicks")
