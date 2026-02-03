# Bitrix24 Telegram Task Bot (MVP)

Telegram-бот на Python создаёт задачи в Bitrix24 через Inbound Webhook. MVP хранит вложения локально и добавляет в описание список путей.

## Возможности

- Команды `/start`, `/task`, `/cancel`.
- Диалог: название → описание → вложения → подтверждение.
- Принимает фото и документы, сохраняет на сервере в `./uploads/<date>/<tg_user_id>/<ticket_id>/`.
- Создаёт задачу через `tasks.task.add`.
- В описание добавляется блок «Инициатор» и «Вложения».
- Ограничение по whitelist (`ALLOWED_TG_USERS`).

## Требования

- Python 3.11+
- Bitrix24 Inbound Webhook с правами на задачи

## Установка (копируй‑вставляй)

```bash
mkdir -p ~/bitrix_task_bot
cd ~/bitrix_task_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Заполните `.env` (см. ниже).

## Запуск

```bash
source .venv/bin/activate
python main.py
```

## Настройка Bitrix24 (Inbound Webhook)

1. Зайдите в Bitrix24 под пользователем, у которого есть доступ к задачам.
2. Откройте **Разработчикам** → **Вебхуки**.
3. Нажмите **Добавить входящий вебхук**.
4. Укажите права: **Задачи (tasks)**.
5. Сохраните и скопируйте URL вида:
   `https://<portal>.bitrix24.ru/rest/<user_id>/<token>/`
6. Этот URL используйте в `BITRIX_WEBHOOK_BASE`.
7. Получите ID ответственного пользователя (в задаче Bitrix) и укажите в `BITRIX_DEFAULT_RESPONSIBLE_ID`.

## Переменные окружения

См. `.env.example`:

```env
TG_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
BITRIX_WEBHOOK_BASE=https://yourportal.bitrix24.ru/rest/1/yourtoken/
BITRIX_DEFAULT_RESPONSIBLE_ID=123
BITRIX_GROUP_ID=
BITRIX_PRIORITY=
BITRIX_PORTAL_BASE=https://yourportal.bitrix24.ru
ALLOWED_TG_USERS=111,222
UPLOAD_DIR=./uploads
LOG_LEVEL=INFO
```

- `ALLOWED_TG_USERS`: список TG ID через запятую. Если пусто — доступ открыт всем.
- `BITRIX_GROUP_ID`, `BITRIX_PRIORITY` — опционально.
- `BITRIX_PORTAL_BASE` — нужен для ссылки на задачу.

## Поведение бота

- `/start` → приветствие + кнопка «Создать задачу»
- `/task` → старт диалога
- `/cancel` → отмена

## Проверка работы (мини‑чеклист)

1. Запустите бота.
2. В Telegram: `/start` → «Создать задачу».
3. Введите название и описание.
4. Прикрепите пару файлов/скриншотов.
5. Нажмите «Готово ✅» → «Создать ✅».
6. Убедитесь, что задача появилась в Bitrix24 и в описании есть блоки «Инициатор» и «Вложения».

## Частые ошибки и решения

- **401/403 Bitrix**: неверный webhook или нет прав `tasks`.
- **Telegram Conflict**: бот запущен в двух местах — остановите лишний процесс.
- **`py` не найден**: используйте `python3 -m venv .venv`.
- **Файлы не сохраняются**: проверьте права на папку `UPLOAD_DIR`.

## Systemd (опционально)

Пример `/etc/systemd/system/bitrix_tg_bot.service`:

```ini
[Unit]
Description=Bitrix24 Telegram Task Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/bitrix_task_bot
EnvironmentFile=/home/ubuntu/bitrix_task_bot/.env
ExecStart=/home/ubuntu/bitrix_task_bot/.venv/bin/python /home/ubuntu/bitrix_task_bot/main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Команды:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bitrix_tg_bot
sudo systemctl start bitrix_tg_bot
sudo systemctl status bitrix_tg_bot
sudo journalctl -u bitrix_tg_bot -f
```
