from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import api_router
from app.services.scraping import Scraping


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    scraping = Scraping(settings.scrape_interval_seconds)
    thread = Thread(
        target=scraping.loop,
        daemon=True,
        name="scraping-loop",
    )
    thread.start()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Prisma News API", lifespan=lifespan)

    if settings.allowed_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router)

    return app


app = create_app()
