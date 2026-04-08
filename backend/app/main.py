from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.db import neo4j_driver, minio_client, seed
from app.health.router import router as health_router
from app.auth.router import router as auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    neo4j_driver.connect(settings.NEO4J_URI, settings.NEO4J_AUTH)
    minio_client.connect(
        settings.MINIO_ENDPOINT,
        settings.MINIO_ROOT_USER,
        settings.MINIO_ROOT_PASSWORD,
        settings.MINIO_BUCKET,
    )
    seed.run_seed(neo4j_driver.get_driver(), settings)
    yield
    neo4j_driver.close()


app = FastAPI(title="Memograph", lifespan=lifespan)
app.include_router(health_router)
app.include_router(auth_router)
