from fastapi import APIRouter
from app.db.neo4j_driver import get_driver
from app.db.minio_client import get_client

router = APIRouter(prefix="/api/health", tags=["health"])

@router.get("/")
async def health_check():
    try:
        get_driver().verify_connectivity()
        get_client().list_buckets()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
