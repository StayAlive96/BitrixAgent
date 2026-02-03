from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


@dataclass
class BitrixTaskResult:
    task_id: int
    task_url: str | None


class BitrixClient:
    def __init__(self, webhook_base: str) -> None:
        self._webhook_base = webhook_base.rstrip("/") + "/"
        self._timeout = httpx.Timeout(10.0, connect=5.0)

    async def create_task(self, title: str, description: str) -> BitrixTaskResult:
        url = f"{self._webhook_base}tasks.task.add"
        payload = {
            "fields[TITLE]": title,
            "fields[DESCRIPTION]": description,
            "fields[RESPONSIBLE_ID]": settings.bitrix_default_responsible_id,
        }
        if settings.bitrix_group_id:
            payload["fields[GROUP_ID]"] = settings.bitrix_group_id
        if settings.bitrix_priority:
            payload["fields[PRIORITY]"] = settings.bitrix_priority

        logger.info("Sending task to Bitrix")
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, data=payload)
        data = response.json()
        if response.status_code >= 400 or "error" in data:
            error_desc = data.get("error_description") or data.get("error") or "Unknown Bitrix error"
            raise RuntimeError(f"Bitrix API error: {error_desc}")

        task_id = _extract_task_id(data)
        task_url = None
        if settings.bitrix_portal_base:
            base = settings.bitrix_portal_base.rstrip("/")
            task_url = f"{base}/company/personal/user/{settings.bitrix_default_responsible_id}/tasks/task/view/{task_id}/"
        return BitrixTaskResult(task_id=task_id, task_url=task_url)


def _extract_task_id(data: dict[str, Any]) -> int:
    result = data.get("result") or {}
    task = result.get("task") or {}
    task_id = task.get("id") or result.get("task_id") or result.get("id")
    if task_id is None:
        raise RuntimeError("Bitrix API response missing task id")
    return int(task_id)
