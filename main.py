import os
from ui.telegramBot import run_bot


if __name__ == "__main__":
    TOKEN = os.getenv("8171993764:AAEvLxlKpdPyo97w_SHlNoXWRXvuw0LWXDU")
    if not TOKEN:
        raise RuntimeError(
            "Telegram bot token is not set. "
            "Set TELEGRAM_BOT_TOKEN environment variable."
        )
    run_bot(TOKEN)
