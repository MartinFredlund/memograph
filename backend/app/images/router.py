from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from neo4j import Session

from app.auth.schemas import TokenPayload
from app.dependencies import get_db_session, require_editor
from app.images.schemas import ImageResponse, ImageRotate, TagCreate, TagResponse
from app.images.service import (
    DeleteResult,
    TagResult,
    add_tag,
    create_image,
    delete_image,
    rotate_image,
)

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/{uid}/rotate")
def rotate(
    uid: str,
    data: ImageRotate,
    session: Session = Depends(get_db_session),
    current_user=Depends(require_editor),
) -> ImageResponse:
    image = rotate_image(session, uid, data.degrees)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return ImageResponse(**image)


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


@router.delete("/{uid}", status_code=204)
def delete(
    uid: str,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_editor),
) -> None:
    result = delete_image(session, uid, current_user)
    if result == DeleteResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail="Image not found")
    if result == DeleteResult.FORBIDDEN:
        raise HTTPException(
            status_code=403, detail="You can only delete your own uploads"
        )


@router.post("/{uid}/tags", status_code=201)
def add_tag_endpoint(
    uid: str,
    data: TagCreate,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_editor),
) -> TagResponse:
    result, payload = add_tag(session, uid, data.person_uid, data.tag_x, data.tag_y)
    if result == TagResult.IMAGE_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Image not found")
    if result == TagResult.PERSON_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Person not found")
    return TagResponse(**payload)
