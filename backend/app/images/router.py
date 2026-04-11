from fastapi import APIRouter, Depends, File, UploadFile
from neo4j import Session

from app.dependencies import get_db_session, require_editor
from app.images.schemas import ImageResponse
from app.images.service import create_image


router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/", status_code=201)
async def upload(
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
) -> list[ImageResponse]:
    created = []
    for file in files:
        content = await file.read()
        image = create_image(
            session=session,
            uploader_uid=current_user.sub,
            filename=file.filename or "unknown",
            content=content,
            content_type=file.content_type or "application/octet-stream",
        )
        created.append(ImageResponse(**image))
    return created
