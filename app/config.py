import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    IVASMS_EMAIL = os.getenv("IVASMS_EMAIL")
    IVASMS_PASSWORD = os.getenv("IVASMS_PASSWORD")

    REQUIRED_ENV_VARS = [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHAT_ID",
        "IVASMS_EMAIL",
        "IVASMS_PASSWORD",
    ]

    @classmethod
    def validate(cls):
        missing_vars = [var for var in cls.REQUIRED_ENV_VARS if getattr(cls, var) is None]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

