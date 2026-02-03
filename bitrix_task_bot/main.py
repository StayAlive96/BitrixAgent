import logging

from telegram.ext import Application, CommandHandler, ConversationHandler, MessageHandler, filters

from bot_handlers import (
    CONFIRM,
    WAIT_ATTACHMENTS,
    WAIT_DESCRIPTION,
    WAIT_TITLE,
    cancel,
    confirm,
    start,
    task_entry,
    wait_attachments,
    wait_description,
    wait_title,
)
from config import settings, validate_settings


def setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def on_startup(app: Application) -> None:
    app.bot_data["webhook_base"] = settings.bitrix_webhook_base



def build_application() -> Application:
    validate_settings()
    app = Application.builder().token(settings.tg_bot_token).post_init(on_startup).build()

    conversation = ConversationHandler(
        entry_points=[
            CommandHandler("task", task_entry),
            MessageHandler(filters.Regex("^Создать задачу$"), task_entry),
        ],
        states={
            WAIT_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, wait_title)],
            WAIT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, wait_description)],
            WAIT_ATTACHMENTS: [
                MessageHandler(
                    filters.PHOTO | filters.Document.ALL | filters.TEXT & ~filters.COMMAND,
                    wait_attachments,
                )
            ],
            CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conversation)
    app.add_handler(CommandHandler("cancel", cancel))
    return app


def main() -> None:
    setup_logging()
    app = build_application()
    app.run_polling()


if __name__ == "__main__":
    main()
