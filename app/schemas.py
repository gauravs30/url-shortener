"""Request/response models for the JSON API."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class LinkCreate(BaseModel):
    url: str = Field(description="Absolute http(s) URL to shorten")
    alias: str | None = Field(default=None, description="Optional custom short code")
    ttl_days: int | None = Field(default=None, ge=0, description="Expire this many days from now")
    expires_at: datetime | None = Field(default=None, description="Explicit expiry timestamp")

    @field_validator("url")
    @classmethod
    def _http_scheme(cls, v: str) -> str:
        v = v.strip()
        if not v.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        return v

    @model_validator(mode="after")
    def _one_expiry_form(self) -> "LinkCreate":
        if self.ttl_days is not None and self.expires_at is not None:
            raise ValueError("provide only one of ttl_days or expires_at")
        return self


class LinkOut(BaseModel):
    code: str
    short_url: str
    target_url: str
    created_at: datetime
    expires_at: datetime | None


class ClickOut(BaseModel):
    ts: datetime
    referrer: str | None
    user_agent: str | None


class DayCount(BaseModel):
    day: str  # YYYY-MM-DD (UTC)
    count: int


class LinkStats(BaseModel):
    code: str
    target_url: str
    created_at: datetime
    expires_at: datetime | None
    total_clicks: int
    clicks_by_day: list[DayCount]
    recent_clicks: list[ClickOut]
