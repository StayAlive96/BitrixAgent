from __future__ import annotations

import datetime as dt
import os
from dataclasses import dataclass
from pathlib import Path

from telegram import File

from config import settings


@dataclass
class StoredFile:
    name: str
    path: Path


async def save_telegram_file(file: File, filename: str, tg_user_id: int, ticket_id: str) -> StoredFile:
    base_dir = Path(settings.upload_dir)
    date_dir = dt.datetime.now().strftime("%Y-%m-%d")
    target_dir = base_dir / date_dir / str(tg_user_id) / ticket_id
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _sanitize_filename(filename)
    target_path = target_dir / safe_name
    await file.download_to_drive(custom_path=str(target_path))
    return StoredFile(name=safe_name, path=target_path)



def _sanitize_filename(name: str) -> str:
    name = name.strip().replace("/", "_").replace("\\", "_")
    if not name:
        return "file"
    return name
