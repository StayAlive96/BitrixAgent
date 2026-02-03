import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _get_env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


@dataclass(frozen=True)
class Settings:
    tg_bot_token: str
    bitrix_webhook_base: str
    bitrix_default_responsible_id: int
    bitrix_group_id: int | None
    bitrix_priority: int | None
    bitrix_portal_base: str | None
    allowed_tg_users: set[int] | None
    upload_dir: str
    log_level: str



def _parse_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)



def _parse_allowed_users(value: str | None) -> set[int] | None:
    if value is None or value.strip() == "":
        return None
    ids = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        ids.add(int(item))
    return ids if ids else None


settings = Settings(
    tg_bot_token=_get_env("TG_BOT_TOKEN", ""),
    bitrix_webhook_base=_get_env("BITRIX_WEBHOOK_BASE", ""),
    bitrix_default_responsible_id=int(_get_env("BITRIX_DEFAULT_RESPONSIBLE_ID", "0") or 0),
    bitrix_group_id=_parse_int(_get_env("BITRIX_GROUP_ID")),
    bitrix_priority=_parse_int(_get_env("BITRIX_PRIORITY")),
    bitrix_portal_base=_get_env("BITRIX_PORTAL_BASE"),
    allowed_tg_users=_parse_allowed_users(_get_env("ALLOWED_TG_USERS")),
    upload_dir=_get_env("UPLOAD_DIR", "./uploads") or "./uploads",
    log_level=_get_env("LOG_LEVEL", "INFO") or "INFO",
)



def validate_settings() -> None:
    if not settings.tg_bot_token:
        raise ValueError("TG_BOT_TOKEN is required")
    if not settings.bitrix_webhook_base:
        raise ValueError("BITRIX_WEBHOOK_BASE is required")
    if settings.bitrix_default_responsible_id <= 0:
        raise ValueError("BITRIX_DEFAULT_RESPONSIBLE_ID must be set")
