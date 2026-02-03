from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Iterable

from telegram import User

from config import settings
from storage import StoredFile


@dataclass
class InitiatorInfo:
    name: str
    username: str | None
    tg_id: int



def build_description(user_description: str, initiator: InitiatorInfo, files: Iterable[StoredFile]) -> str:
    timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        user_description.strip(),
        "",
        "Инициатор:",
        f"Имя: {initiator.name}",
        f"Username: {initiator.username or '-'}",
        f"TG ID: {initiator.tg_id}",
        f"Дата/время: {timestamp}",
        "",
        "Вложения:",
    ]
    file_list = list(files)
    if not file_list:
        lines.append("- нет")
    else:
        for file in file_list:
            lines.append(f"- {file.name} ({file.path})")
    return "\n".join(lines)



def user_to_initiator(user: User) -> InitiatorInfo:
    name = " ".join(part for part in [user.first_name, user.last_name] if part)
    return InitiatorInfo(name=name or user.username or "Unknown", username=user.username, tg_id=user.id)



def is_allowed(user_id: int) -> bool:
    if settings.allowed_tg_users is None:
        return True
    return user_id in settings.allowed_tg_users
