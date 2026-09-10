"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import get_engine
from app.limiter import limiter
from app.routes import health, links, redirect

_HERE = Path(__file__).parent
templates = Jinja2Templates(directory=str(_HERE / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_engine()  # build the engine/sessionmaker eagerly so first request is warm
    yield
    engine = get_engine()
    await engine.dispose()


app = FastAPI(title="url-shortener", version="0.1.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Order matters: specific routes first, the /{code} catch-all last.
app.include_router(health.router)
app.include_router(links.router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request, "index.html", {"base_url": get_settings().base_url.rstrip("/")}
    )


app.mount("/static", StaticFiles(directory=str(_HERE / "static")), name="static")
app.include_router(redirect.router)
