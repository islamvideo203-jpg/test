import asyncio
import logging
from app.config import Config
from app.scraper import IvaSmsScraper
from app.bot import TelegramBot
from app.utils import setup_logging
from telegram.ext import Application

logger = setup_logging()

async def main():
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        return

    telegram_bot_token = Config.TELEGRAM_BOT_TOKEN
    telegram_chat_id = Config.TELEGRAM_CHAT_ID
    ivasms_email = Config.IVASMS_EMAIL
    ivasms_password = Config.IVASMS_PASSWORD

    scraper = IvaSmsScraper(ivasms_email, ivasms_password)
    bot = TelegramBot(telegram_bot_token, telegram_chat_id, scraper)

    logger.info("Starting Telegram bot...")
    # The run method already handles polling, no need for application.run_polling here
    bot.run()

if __name__ == "__main__":
    asyncio.run(main())

