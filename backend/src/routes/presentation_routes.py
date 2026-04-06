from __future__ import annotations

from typing import Annotated, Any
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Response,
    UploadFile,
)
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.auth.dependencies import get_current_user
from src.database import get_db
from src.schemas.presentation_schema import SavePresentationSchema
from src.schemas.presentation_schemas import EditSlideInSchema, GeneratePresInSchema
from src.schemas.user_schemas import Presentation, User
from src.services.convert_file_service import convert_file
from src.services.model_service import edit_one_slide, generate_presentation
from src.services.presentation_json_service import generate_presentation_json
from src.services.pptx_automizer_service import (
    export_presentation_with_automizer,
    get_default_template_info,
    save_default_template,
)

router = APIRouter(prefix="/presentation")


class ExportTemplateRequest(BaseModel):
    slides: list[dict[str, Any]]


@router.get("/my-presentations")
def my_presentations(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return db.query(Presentation).filter_by(user_id=current_user.id).all()


@router.delete("/presentations/{presentation_id}")
def delete_presentation(
    presentation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    pres = (
        db.query(Presentation)
        .filter_by(id=presentation_id, user_id=current_user.id)
        .first()
    )
    if not pres:
        raise HTTPException(status_code=404, detail="Presentation not found")

    db.delete(pres)
    db.commit()
    return {"detail": "Presentation deleted"}


@router.post("/save-presentation")
def save_presentation(
    data: SavePresentationSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not data.id:
        data.id = str(uuid4())
        pres = Presentation(
            id=data.id,
            user_id=current_user.id,
            title=data.title,
            content=data.content,
            theme=data.theme,
        )
        db.add(pres)
    else:
        pres = (
            db.query(Presentation)
            .filter_by(id=data.id, user_id=current_user.id)
            .first()
        )
        if not pres:
            pres = Presentation(
                id=data.id,
                user_id=current_user.id,
                title=data.title,
                content=data.content,
                theme=data.theme,
            )
            db.add(pres)
        else:
            pres.title = data.title
            pres.content = data.content
            pres.theme = data.theme

    db.commit()
    db.refresh(pres)
    return {"id": pres.id, "message": "Presentation saved"}


@router.post("/generate", status_code=201)
async def generate(
    text: Annotated[str, Form(min_length=1)],
    file: Annotated[UploadFile, File()],
    model: Annotated[str, Form()] = "",
    slide_count: Annotated[int, Form()] = 10,
) -> Response:
    body = GeneratePresInSchema(text=text, model=model, slide_count=slide_count)
    context = await convert_file(file)

    return StreamingResponse(
        generate_presentation(body.text, context, body.model, body.slide_count),
        media_type="text/markdown",
    )


@router.post("/generate-json", status_code=201)
async def generate_json(
    text: Annotated[str, Form(min_length=1)],
    file: Annotated[UploadFile, File()],
    model: Annotated[str, Form()] = "",
    slide_count: Annotated[int, Form()] = 10,
) -> JSONResponse:
    body = GeneratePresInSchema(text=text, model=model, slide_count=slide_count)
    context = await convert_file(file)
    payload = await generate_presentation_json(
        body.text,
        context,
        body.model,
        body.slide_count,
    )
    return JSONResponse(content=payload)


@router.post("/export-template", status_code=200)
async def export_template(body: ExportTemplateRequest) -> Response:
    content, filename = await export_presentation_with_automizer(body.slides)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers=headers,
    )


@router.post("/export-template-with-upload", status_code=200)
async def export_template_with_upload(
    slides_json: Annotated[str, Form()],
    template_file: Annotated[UploadFile, File()],
) -> Response:
    import json

    try:
        payload = json.loads(slides_json)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="slides_json должен быть валидным JSON") from exc

    if isinstance(payload, dict):
        slides = payload.get("slides") or []
    elif isinstance(payload, list):
        slides = payload
    else:
        raise HTTPException(status_code=400, detail="slides_json должен содержать slides")

    content, filename = await export_presentation_with_automizer(slides, template_file)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers=headers,
    )


@router.get("/default-template", status_code=200)
def default_template_info() -> JSONResponse:
    return JSONResponse(content=get_default_template_info())


@router.post("/default-template", status_code=200)
async def upload_default_template(
    template_file: Annotated[UploadFile, File()],
) -> JSONResponse:
    result = await save_default_template(template_file)
    return JSONResponse(content=result)


@router.post("/edit", status_code=200)
async def edit(body: EditSlideInSchema) -> Response:
    model_res = edit_one_slide(body.text, body.slide, body.action, body.model)
    return Response(content=model_res, media_type="text/markdown")
