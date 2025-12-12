from ui.telegramBot import run_bot

try:
    from config import TELEGRAM_BOT_TOKEN
except ImportError:
    raise RuntimeError(
        "Missing config.py. "
        
        "Copy config_example.py to config.py and set TELEGRAM_BOT_TOKEN there."
    )


if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN in config.py is empty.")
    run_bot(TELEGRAM_BOT_TOKEN)
