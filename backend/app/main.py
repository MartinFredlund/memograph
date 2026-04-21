from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.db import neo4j_driver, minio_client, seed
from app.health.router import router as health_router
from app.auth.router import router as auth_router
from app.people.router import router as people_router
from app.relationships.router import router as relationships_router
from app.events.router import router as events_router
from app.places.router import router as places_router
from app.images.router import router as images_router
from app.graph.router import router as graph_router


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
app.include_router(people_router)
app.include_router(relationships_router)
app.include_router(events_router)
app.include_router(places_router)
app.include_router(images_router)
app.include_router(graph_router)
