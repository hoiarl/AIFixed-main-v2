from __future__ import annotations

import html
import re
from uuid import uuid4
from typing import Any

from src.config import settings
from src.services.model_service import IntegratedPipeline, api_key


def _strip_markdown(text: str) -> str:
    text = re.sub(r"^#+\s*", "", text.strip(), flags=re.MULTILINE)
    return text.strip()


def _split_content(content: str) -> tuple[list[str], list[str]]:
    paragraphs: list[str] = []
    bullets: list[str] = []
    current_paragraph: list[str] = []

    for raw_line in (content or "").splitlines():
        line = raw_line.strip()
        if not line:
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph).strip())
                current_paragraph = []
            continue

        bullet_match = re.match(r"^(?:[*\-•]|\d+[\.)])\s+(.*)$", line)
        if bullet_match:
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph).strip())
                current_paragraph = []
            bullets.append(bullet_match.group(1).strip())
            continue

        current_paragraph.append(_strip_markdown(line))

    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph).strip())

    paragraphs = [p for p in paragraphs if p]
    bullets = [b for b in bullets if b]
    return paragraphs, bullets


def _build_body_html(paragraphs: list[str], bullets: list[str]) -> str:
    parts = ["<html><body>"]
    for paragraph in paragraphs:
        parts.append(f"<p>{html.escape(paragraph)}</p>")
    if bullets:
        parts.append("<ul>")
        for bullet in bullets:
            parts.append(f"<li>{html.escape(bullet)}</li>")
        parts.append("</ul>")
    parts.append("</body></html>")
    return "".join(parts)


def _build_blocks(title: str, paragraphs: list[str], bullets: list[str]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = [
        {
            "id": str(uuid4()),
            "type": "heading",
            "text": title,
            "style": {
                "fontWeight": 700,
                "fontSize": 28,
            },
        }
    ]

    y_cursor = 16
    if paragraphs:
        lead = paragraphs[0]
        blocks.append(
            {
                "id": str(uuid4()),
                "type": "paragraph",
                "text": lead,
                "style": {
                    "fontSize": 17,
                    "fontWeight": 400,
                },
                "xPercent": 8,
                "yPercent": y_cursor,
                "widthPercent": 84,
                "heightPercent": 18,
            }
        )
        y_cursor = 36

        for extra_paragraph in paragraphs[1:]:
            blocks.append(
                {
                    "id": str(uuid4()),
                    "type": "paragraph",
                    "text": extra_paragraph,
                    "style": {
                        "fontSize": 15,
                        "fontWeight": 400,
                    },
                    "xPercent": 8,
                    "yPercent": y_cursor,
                    "widthPercent": 84,
                    "heightPercent": 12,
                }
            )
            y_cursor += 12

    if bullets:
        blocks.append(
            {
                "id": str(uuid4()),
                "type": "list",
                "items": bullets,
                "richParts": [[{"text": bullet}] for bullet in bullets],
                "style": {
                    "fontSize": 15,
                    "fontWeight": 400,
                },
                "xPercent": 8,
                "yPercent": min(y_cursor, 46),
                "widthPercent": 84,
                "heightPercent": 36,
            }
        )

    return blocks


def normalize_generated_slide(raw_slide: dict[str, Any], position: int) -> dict[str, Any]:
    title = (raw_slide.get("title") or f"Слайд {position}").strip()
    content = (raw_slide.get("content") or "").strip()
    paragraphs, bullets = _split_content(content)
    subtitle = paragraphs[0] if paragraphs else ""

    if not paragraphs and not bullets and content:
        paragraphs = [_strip_markdown(content)]
        subtitle = paragraphs[0]

    return {
        "id": str(uuid4()),
        "title": title,
        "layout": "text-only",
        "markdownText": f"# {title}\n\n{content}".strip(),
        "content": _build_blocks(title, paragraphs, bullets),
        "templateBinding": {
            "kind": "cover" if position == 1 else "content",
            "layoutKey": "cover" if position == 1 else "content",
            "title": title,
            "subtitle": subtitle,
            "paragraphs": paragraphs,
            "bullets": bullets,
            "bodyHtml": _build_body_html(paragraphs, bullets),
            "rawContent": content,
        },
    }


async def generate_presentation_json(
    user_prompt: str,
    project_context: str,
    model: str,
    slide_count: int | None = None,
) -> dict[str, Any]:
    pipe = IntegratedPipeline(
        api_key=api_key,
        embedding_model=settings.DEFAULT_EMBEDDING_MODEL,
        llm_model=model or settings.DEFAULT_MODEL,
    )
    pipe.load_documents([project_context])

    slides: list[dict[str, Any]] = []
    for idx, slide in enumerate(
        pipe.run(user_prompt, project_context=project_context, slide_count=slide_count),
        start=1,
    ):
        slides.append(normalize_generated_slide(slide, idx))

    return {
        "slides": slides,
        "templateMode": "pptx-automizer",
        "templateRequired": True,
        "exportEngine": "server-template-automizer",
    }
