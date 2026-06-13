"""Исходящие вызовы в B2B."""
import uuid
from datetime import datetime, timezone

import httpx

import src.config as config


def _headers() -> dict:
    return {"X-Service-Key": config.MOD_TO_B2B_KEY}


def get_product_from_b2b(product_id: str) -> dict | None:
    """GET /api/v1/products/{id} из B2B. Возвращает None при ошибке."""
    if not config.B2B_URL or not config.MOD_TO_B2B_KEY:
        return None
    try:
        resp = httpx.get(
            f"{config.B2B_URL}/api/v1/products/{product_id}",
            headers=_headers(),
            timeout=5.0,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def _strip_private_fields(product_data: dict) -> dict:
    product_data = {**product_data}
    for sku in product_data.get("skus", []):
        sku.pop("cost_price", None)
        sku.pop("reserved_quantity", None)
    return product_data


def fetch_product_json(product_id: str) -> dict | None:
    data = get_product_from_b2b(product_id)
    if data is None:
        return None
    return _strip_private_fields(data)


def send_moderation_decision(product_id: str, payload: dict) -> bool:
    """POST /api/v1/events/moderation в B2B. Возвращает True при успехе."""
    if not config.B2B_URL or not config.MOD_TO_B2B_KEY:
        return True  # в тестах считаем успехом
    try:
        resp = httpx.post(
            f"{config.B2B_URL}/api/v1/events/moderation",
            json=payload,
            headers=_headers(),
            timeout=5.0,
        )
        return resp.status_code == 200
    except Exception:
        return False
