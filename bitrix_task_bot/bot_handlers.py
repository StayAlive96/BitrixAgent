from __future__ import annotations

import logging
import uuid
from typing import Any

from telegram import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import ContextTypes

from bitrix import BitrixClient
from storage import save_telegram_file
from utils import build_description, is_allowed, user_to_initiator

logger = logging.getLogger(__name__)

WAIT_TITLE, WAIT_DESCRIPTION, WAIT_ATTACHMENTS, CONFIRM = range(4)

KEY_START = "start"
KEY_TITLE = "title"
KEY_DESCRIPTION = "description"
KEY_FILES = "files"
KEY_TICKET_ID = "ticket_id"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _ensure_allowed(update):
        return -1
    keyboard = [[KeyboardButton("Создать задачу")]]
    await update.message.reply_text(
        "Привет! Я помогу создать задачу в Bitrix24.\n" "Нажмите кнопку ниже или используйте /task.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return -1


async def task_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _ensure_allowed(update):
        return -1
    logger.info("Starting task dialog")
    context.user_data.clear()
    context.user_data[KEY_TICKET_ID] = uuid.uuid4().hex[:8]
    await update.message.reply_text("Введите название задачи:", reply_markup=ReplyKeyboardRemove())
    return WAIT_TITLE


async def wait_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _ensure_allowed(update):
        return -1
    title = (update.message.text or "").strip()
    if not title:
        await update.message.reply_text("Название не может быть пустым. Введите снова:")
        return WAIT_TITLE
    context.user_data[KEY_TITLE] = title
    logger.info("Got title")
    await update.message.reply_text("Введите описание задачи:")
    return WAIT_DESCRIPTION


async def wait_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _ensure_allowed(update):
        return -1
    description = (update.message.text or "").strip()
    if not description:
        await update.message.reply_text("Описание не может быть пустым. Введите снова:")
        return WAIT_DESCRIPTION
    context.user_data[KEY_DESCRIPTION] = description
    context.user_data[KEY_FILES] = []
    logger.info("Got description")

    keyboard = [[KeyboardButton("Готово ✅")]]
    await update.message.reply_text(
        "Пришлите скриншоты или файлы (можно несколько). Когда закончите, нажмите 'Готово ✅'.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return WAIT_ATTACHMENTS


async def wait_attachments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _ensure_allowed(update):
        return -1
    message = update.message
    if message.text and message.text.strip() == "Готово ✅":
        return await _confirm(update, context)

    if message.photo:
        photo = message.photo[-1]
        file = await photo.get_file()
        filename = f"photo_{photo.file_id}.jpg"
        stored = await save_telegram_file(
            file,
            filename,
            tg_user_id=message.from_user.id,
            ticket_id=context.user_data[KEY_TICKET_ID],
        )
        context.user_data[KEY_FILES].append(stored)
        logger.info("Saved photo")
        await message.reply_text("Фото сохранено. Можете отправить ещё или нажмите 'Готово ✅'.")
        return WAIT_ATTACHMENTS

    if message.document:
        document = message.document
        file = await document.get_file()
        filename = document.file_name or f"document_{document.file_id}"
        stored = await save_telegram_file(
            file,
            filename,
            tg_user_id=message.from_user.id,
            ticket_id=context.user_data[KEY_TICKET_ID],
        )
        context.user_data[KEY_FILES].append(stored)
        logger.info("Saved document")
        await message.reply_text("Файл сохранён. Можете отправить ещё или нажмите 'Готово ✅'.")
        return WAIT_ATTACHMENTS

    await message.reply_text("Пожалуйста, отправьте фото/файл или нажмите 'Готово ✅'.")
    return WAIT_ATTACHMENTS


async def _confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    keyboard = [[KeyboardButton("Создать ✅"), KeyboardButton("Отмена ❌")]]
    await update.message.reply_text(
        "Проверьте данные и нажмите 'Создать ✅' для отправки в Bitrix.",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
    )
    return CONFIRM


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _ensure_allowed(update):
        return -1
    text = (update.message.text or "").strip()
    if text == "Отмена ❌":
        await update.message.reply_text("Создание отменено.", reply_markup=ReplyKeyboardRemove())
        context.user_data.clear()
        return -1
    if text != "Создать ✅":
        await update.message.reply_text("Пожалуйста, выберите 'Создать ✅' или 'Отмена ❌'.")
        return CONFIRM

    title = context.user_data.get(KEY_TITLE)
    description = context.user_data.get(KEY_DESCRIPTION)
    files = context.user_data.get(KEY_FILES, [])
    if not title or not description:
        await update.message.reply_text("Данные не найдены. Начните заново через /task.")
        return -1

    initiator = user_to_initiator(update.message.from_user)
    full_description = build_description(description, initiator, files)

    logger.info("Creating task in Bitrix")
    client = BitrixClient(webhook_base=context.application.bot_data["webhook_base"])
    try:
        result = await client.create_task(title=title, description=full_description)
    except Exception as exc:
        logger.exception("Bitrix create task failed")
        await update.message.reply_text(f"Ошибка при создании задачи: {exc}")
        return -1

    response_lines = ["Задача создана ✅", f"ID: {result.task_id}"]
    if result.task_url:
        response_lines.append(f"Ссылка: {result.task_url}")
    else:
        response_lines.append("Ссылку можно добавить позже через BITRIX_PORTAL_BASE.")

    await update.message.reply_text("\n".join(response_lines), reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return -1


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await _ensure_allowed(update):
        return -1
    context.user_data.clear()
    await update.message.reply_text("Диалог отменён.", reply_markup=ReplyKeyboardRemove())
    return -1


async def _ensure_allowed(update: Update) -> bool:
    user = update.effective_user
    if user is None:
        return False
    if not is_allowed(user.id):
        if update.message:
            await update.message.reply_text("Доступ запрещён. Обратитесь к администратору.")
        return False
    return True
