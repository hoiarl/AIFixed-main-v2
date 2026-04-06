import json
import time
import uuid
from typing import Any

import requests

from src.config import settings, model_settings


_TOKEN_CACHE: dict[str, Any] = {"access_token": None, "expires_at": 0.0, "source": None}


def call_model(
    messages: list[dict],
    api_key: str,
    model: str = settings.DEFAULT_MODEL,
    temperature: float = model_settings.GEN_TEMPERATURE,
    max_tokens: int = 900,
    timeout: int = 60,
) -> dict:
    access_token = get_gigachat_access_token(api_key)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "presenton-stable/1.2",
    }
    payload = {
        "model": model or settings.DEFAULT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    resp = requests.post(
        settings.GIGACHAT_API_URL,
        headers=headers,
        json=payload,
        timeout=timeout,
        verify=settings.GIGACHAT_VERIFY_SSL,
    )
    if resp.status_code == 401 and not settings.GIGACHAT_ACCESS_TOKEN:
        access_token = get_gigachat_access_token(api_key, force_refresh=True)
        headers["Authorization"] = f"Bearer {access_token}"
        resp = requests.post(
            settings.GIGACHAT_API_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
            verify=settings.GIGACHAT_VERIFY_SSL,
        )
    if not resp.ok:
        try:
            err = resp.json()
            raise RuntimeError(
                f"GigaChat API error {resp.status_code}: {json.dumps(err, ensure_ascii=False)}"
            )
        except Exception:
            raise RuntimeError(f"GigaChat API error {resp.status_code}: {resp.text}")
    return resp.json()


def get_content(resp: dict) -> str:
    try:
        return resp["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(
            f"Unexpected LLM response format: {json.dumps(resp, ensure_ascii=False)[:800]}"
        ) from e


def get_api_key(explicit: str | None = None) -> str:
    key = (
        explicit
        or settings.GIGACHAT_ACCESS_TOKEN
        or settings.GIGACHAT_AUTH_KEY
        or settings.OPENROUTER_API_KEY
        or settings.OPENAI_API_KEY
        or ""
    ).strip()
    key = _strip_invisible(key)
    if not key:
        raise RuntimeError(
            "GigaChat credentials required (set env GIGACHAT_AUTH_KEY or GIGACHAT_ACCESS_TOKEN)."
        )
    if not key.isascii():
        raise RuntimeError("API key contains non-ASCII characters.")
    return key


def get_gigachat_access_token(api_key: str | None = None, force_refresh: bool = False) -> str:
    configured_access_token = _strip_invisible(settings.GIGACHAT_ACCESS_TOKEN or "")
    if configured_access_token:
        return configured_access_token

    auth_key = _strip_invisible(api_key or settings.GIGACHAT_AUTH_KEY or "")
    if not auth_key:
        raise RuntimeError(
            "GigaChat auth key is missing. Set GIGACHAT_AUTH_KEY or provide GIGACHAT_ACCESS_TOKEN."
        )

    now = time.time()
    cached_token = _TOKEN_CACHE.get("access_token")
    cached_exp = float(_TOKEN_CACHE.get("expires_at") or 0)
    cached_source = _TOKEN_CACHE.get("source")
    if (
        not force_refresh
        and cached_token
        and cached_source == auth_key
        and cached_exp - now > 60
    ):
        return str(cached_token)

    headers = {
        "Authorization": f"Basic {auth_key}",
        "RqUID": str(uuid.uuid4()),
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": "presenton-stable/1.2",
    }
    resp = requests.post(
        settings.GIGACHAT_AUTH_URL,
        headers=headers,
        data={"scope": settings.GIGACHAT_SCOPE},
        timeout=30,
        verify=settings.GIGACHAT_VERIFY_SSL,
    )
    if not resp.ok:
        try:
            err = resp.json()
            raise RuntimeError(
                f"GigaChat auth error {resp.status_code}: {json.dumps(err, ensure_ascii=False)}"
            )
        except Exception:
            raise RuntimeError(f"GigaChat auth error {resp.status_code}: {resp.text}")

    payload = resp.json()
    access_token = payload.get("access_token")
    expires_at = float(payload.get("expires_at") or (now + 25 * 60))
    if not access_token:
        raise RuntimeError(
            f"GigaChat auth response has no access_token: {json.dumps(payload, ensure_ascii=False)}"
        )

    _TOKEN_CACHE.update(
        {
            "access_token": access_token,
            "expires_at": expires_at,
            "source": auth_key,
        }
    )
    return str(access_token)


def _strip_invisible(s: str) -> str:
    if not s:
        return s
    s = "".join(
        ch
        for ch in s
        if ch.isprintable()
        and ch not in ("\u00a0", "\u2009", "\u200a", "\u202f", "\u2007", "\u2060")
    )
    s = s.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")
    return s
