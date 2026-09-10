"""Liveness/readiness probe. Compose uses it as a healthcheck; k8s will use it
for both probes in Phase 2."""

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.database import SessionDep

router = APIRouter(tags=["ops"])


@router.get("/healthz")
async def healthz(session: SessionDep, response: Response) -> dict[str, str]:
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "error", "db": "unreachable"}
    return {"status": "ok", "db": "ok"}
