from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, UploadFile

from src.config import settings


BACKEND_DIR = Path(__file__).resolve().parents[2]
WORKER_DIR = BACKEND_DIR / "pptx_worker"
TEMPLATE_STORAGE_DIR = BACKEND_DIR / "storage" / "templates"
DEFAULT_TEMPLATE_PATH = Path(settings.PRESENTATION_DEFAULT_TEMPLATE_PATH)
DEFAULT_TEMPLATE_CONFIG_PATH = Path(settings.PRESENTATION_DEFAULT_TEMPLATE_CONFIG_PATH)


TEMPLATE_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class TemplateExportError(RuntimeError):
    pass


async def save_default_template(upload: UploadFile) -> dict[str, Any]:
    if not upload.filename or not upload.filename.lower().endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Нужен .pptx шаблон")

    DEFAULT_TEMPLATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    content = await upload.read()
    DEFAULT_TEMPLATE_PATH.write_bytes(content)

    return {
        "ok": True,
        "template_path": str(DEFAULT_TEMPLATE_PATH),
        "config_path": str(DEFAULT_TEMPLATE_CONFIG_PATH),
        "size": len(content),
    }


def get_default_template_info() -> dict[str, Any]:
    return {
        "configured": DEFAULT_TEMPLATE_PATH.exists(),
        "template_path": str(DEFAULT_TEMPLATE_PATH),
        "config_path": str(DEFAULT_TEMPLATE_CONFIG_PATH),
    }


def _extract_text_parts(slide: dict[str, Any]) -> tuple[list[str], list[str]]:
    binding = slide.get("templateBinding") or {}
    paragraphs = [p for p in binding.get("paragraphs") or [] if isinstance(p, str) and p.strip()]
    bullets = [b for b in binding.get("bullets") or [] if isinstance(b, str) and b.strip()]

    if paragraphs or bullets:
        return paragraphs, bullets

    paragraphs = []
    for block in slide.get("content") or []:
        block_type = block.get("type")
        if block_type == "paragraph" and block.get("text"):
            paragraphs.append(str(block["text"]).strip())
        elif block_type in {"list", "ordered-list"}:
            items = block.get("items") or []
            bullets.extend([str(item).strip() for item in items if str(item).strip()])

    return paragraphs, bullets


def _normalize_export_slide(slide: dict[str, Any], index: int) -> dict[str, Any]:
    binding = slide.get("templateBinding") or {}
    paragraphs, bullets = _extract_text_parts(slide)
    subtitle = binding.get("subtitle") or (paragraphs[0] if paragraphs else "")
    raw_content = binding.get("rawContent") or "\n".join(
        [*paragraphs, *[f"• {item}" for item in bullets]]
    )

    return {
        "kind": binding.get("kind") or ("cover" if index == 1 else "content"),
        "layoutKey": binding.get("layoutKey") or ("cover" if index == 1 else "content"),
        "title": slide.get("title") or binding.get("title") or f"Слайд {index}",
        "subtitle": subtitle,
        "paragraphs": paragraphs,
        "bullets": bullets,
        "rawContent": raw_content,
        "bodyHtml": binding.get("bodyHtml") or None,
    }


def _resolve_template_paths(template_override_path: str | None = None) -> tuple[Path, Path | None]:
    template_path = Path(template_override_path) if template_override_path else DEFAULT_TEMPLATE_PATH
    if not template_path.exists():
        raise HTTPException(
            status_code=400,
            detail=(
                "Шаблон по умолчанию не найден. Загрузите его через "
                "POST /presentation/default-template или укажите путь в "
                "PRESENTATION_DEFAULT_TEMPLATE_PATH."
            ),
        )

    config_path = template_path.with_suffix(".config.json")
    if not config_path.exists() and DEFAULT_TEMPLATE_CONFIG_PATH.exists() and template_path == DEFAULT_TEMPLATE_PATH:
        config_path = DEFAULT_TEMPLATE_CONFIG_PATH
    if not config_path.exists():
        config_path = None

    return template_path, config_path


async def export_presentation_with_automizer(
    slides: list[dict[str, Any]],
    template_file: UploadFile | None = None,
) -> tuple[bytes, str]:
    if not slides:
        raise HTTPException(status_code=400, detail="Нет слайдов для экспорта")

    template_override_path: str | None = None
    temp_template_dir: tempfile.TemporaryDirectory[str] | None = None

    if template_file is not None:
        if not template_file.filename or not template_file.filename.lower().endswith(".pptx"):
            raise HTTPException(status_code=400, detail="template_file должен быть .pptx")
        temp_template_dir = tempfile.TemporaryDirectory()
        temp_dir = Path(temp_template_dir.name)
        template_override_path = str(temp_dir / "uploaded-template.pptx")
        Path(template_override_path).write_bytes(await template_file.read())

    template_path, config_path = _resolve_template_paths(template_override_path)

    export_payload = {
        "slides": [_normalize_export_slide(slide, idx) for idx, slide in enumerate(slides, start=1)]
    }

    with tempfile.TemporaryDirectory() as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        input_json_path = temp_dir / "slides.json"
        output_pptx_path = temp_dir / f"presentation-{uuid4()}.pptx"
        input_json_path.write_text(json.dumps(export_payload, ensure_ascii=False, indent=2), encoding="utf-8")

        node_bin = shutil.which(settings.PRESENTATION_NODE_BIN) or shutil.which("node")
        if not node_bin:
            raise HTTPException(
                status_code=500,
                detail="Node.js не найден. Для template-экспорта нужен node в backend-контейнере.",
            )

        script_path = WORKER_DIR / "export-template.mjs"
        if not script_path.exists():
            raise HTTPException(status_code=500, detail="Скрипт template-экспорта не найден")

        cmd = [
            node_bin,
            str(script_path),
            "--input",
            str(input_json_path),
            "--template",
            str(template_path),
            "--output",
            str(output_pptx_path),
        ]
        if config_path is not None:
            cmd.extend(["--config", str(config_path)])

        env = os.environ.copy()
        env.setdefault("NODE_ENV", "production")

        result = subprocess.run(
            cmd,
            cwd=str(WORKER_DIR),
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

        if result.returncode != 0:
            stderr = (result.stderr or result.stdout or "").strip()
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка pptx-automizer: {stderr[:4000]}",
            )

        if not output_pptx_path.exists():
            raise HTTPException(status_code=500, detail="pptx-automizer не создал выходной .pptx")

        content = output_pptx_path.read_bytes()

    if temp_template_dir is not None:
        temp_template_dir.cleanup()

    return content, f"presentation-template-{uuid4().hex[:8]}.pptx"
