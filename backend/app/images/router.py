from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
)
from fastapi.responses import RedirectResponse
from neo4j import Session

from app.auth.schemas import TokenPayload
from app.dependencies import get_db_session, require_editor, get_current_user
from app.images.schemas import (
    EventLink,
    ImageCountParams,
    ImageCountResponse,
    ImageListParams,
    ImageResponse,
    ImageRotate,
    PaginatedImages,
    PersonTagCreate,
    PersonTagResponse,
    PlaceLink,
)
from app.images.service import (
    DeleteResult,
    EventResult,
    PlaceResult,
    TagResult,
    add_tag,
    count_images,
    create_image,
    delete_image,
    get_download_url,
    list_images,
    remove_tag,
    rotate_image,
    set_event,
    set_place,
    unset_event,
    unset_place,
)

router = APIRouter(prefix="/api/images", tags=["images"])


@router.post("/{uid}/rotate")
def rotate(
    uid: str,
    data: ImageRotate,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_editor),
) -> ImageResponse:
    image = rotate_image(session, uid, data.degrees)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return ImageResponse(**image)


@router.post("/", status_code=201)
async def upload(
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_editor),
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
    data: PersonTagCreate,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_editor),
) -> PersonTagResponse:
    result, payload = add_tag(session, uid, data.person_uid, data.tag_x, data.tag_y)
    if result == TagResult.IMAGE_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Image not found")
    if result == TagResult.PERSON_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Person not found")
    return PersonTagResponse(**payload)


@router.delete("/{uid}/tags/{person_uid}", status_code=204)
def remove_tag_endpoint(
    uid: str,
    person_uid: str,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_editor),
) -> None:
    result = remove_tag(session, uid, person_uid)
    if result == TagResult.PERSON_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Person not found")
    if result == TagResult.IMAGE_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Image not found")


@router.put("/{uid}/place", status_code=204)
def set_place_endpoint(
    uid: str,
    data: PlaceLink,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_editor),
) -> None:
    result = set_place(session, uid, data.place_uid)
    if result == PlaceResult.PLACE_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Place not found")
    if result == PlaceResult.IMAGE_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Image not found")


@router.delete("/{uid}/place", status_code=204)
def unset_place_endpoint(
    uid: str,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_editor),
) -> None:
    result = unset_place(session, uid)
    if result == PlaceResult.IMAGE_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Image not found")


@router.put("/{uid}/event", status_code=204)
def set_event_endpoint(
    uid: str,
    data: EventLink,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_editor),
) -> None:
    result = set_event(session, uid, data.event_uid)
    if result == EventResult.IMAGE_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Image not found")
    if result == EventResult.EVENT_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Event not found")


@router.delete("/{uid}/event", status_code=204)
def unset_event_endpoint(
    uid: str,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(require_editor),
) -> None:
    result = unset_event(session, uid)
    if result == EventResult.IMAGE_NOT_FOUND:
        raise HTTPException(status_code=404, detail="Image not found")


@router.get("/{uid}/download")
def download_image(
    uid: str,
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> RedirectResponse:
    url = get_download_url(session, uid)
    if url is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return RedirectResponse(url=url, status_code=302)


@router.get("/", status_code=200)
def list_images_endpoint(
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(get_current_user),
    params: ImageListParams = Depends(),
) -> PaginatedImages:
    try:
        return list_images(session, params)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid cursor")


@router.get("/count", status_code=200)
def count_images_endpoint(
    session: Session = Depends(get_db_session),
    current_user: TokenPayload = Depends(get_current_user),
    params: ImageCountParams = Depends(),
) -> ImageCountResponse:
    return count_images(session, params)
