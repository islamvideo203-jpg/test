import logging
import os
import re
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from app.scraper import IvaSmsScraper
from app.config import Config

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Conversation states for get_old_otps_command
DATE_INPUT = 0

class TelegramBot:
    def __init__(self, token, chat_id, scraper_instance: IvaSmsScraper):
        self.token = token
        self.chat_id = int(chat_id) # Ensure chat_id is an integer
        self.scraper = scraper_instance
        self.application = Application.builder().token(self.token).build()
        self.bot_status = "Initializing..."
        self.scraper.notification_callback = self.send_message # Set the callback

        # Register command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("restart", self.restart_command))
        self.application.add_handler(CommandHandler("last_otp", self.last_otp_command))

        # Conversation handler for /get_old_otps
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("get_old_otps", self.get_old_otps_command)],
            states={
                DATE_INPUT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.receive_dates)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_command)],
        )
        self.application.add_handler(conv_handler)

        # Message handler for unauthorized messages or general text
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.unauthorized_message))

    async def _check_authorized(self, update: Update) -> bool:
        if update.effective_chat.id != self.chat_id:
            await update.message.reply_text("You are not authorized to use this bot.")
            logger.warning(f"Unauthorized access attempt from chat ID: {update.effective_chat.id}")
            return False
        return True

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sends a message when the command /start is issued and initiates login."""
        if not await self._check_authorized(update): return

        user = update.effective_user
        await update.message.reply_html(
            f"Hi {user.mention_html()}! Bot started! Attempting to log in..."
        )
        self.bot_status = "Attempting to log in..."
        await self.send_message("Bot is online and running.")

        if self.scraper.login():
            self.bot_status = "Logged in. Checking for pop-ups..."
            self.scraper.handle_popup()
            
            self.bot_status = "Navigating to OTP page..."
            if self.scraper.navigate_to_otp_page():
                self.bot_status = "Logged in and waiting for OTPs on the statistics page."
                # Start continuous monitoring in a separate task
                # Ensure job is not duplicated if /start is called multiple times
                if 'monitor_job' in context.job_queue.jobs():
                    context.job_queue.get_jobs_by_name('monitor_job')[0].schedule_removal()
                context.job_queue.run_repeating(self.monitor_otps, interval=60, first=0, chat_id=self.chat_id, name='monitor_job')
            else:
                self.bot_status = "Logged in, but failed to navigate to OTP page."
        else:
            self.bot_status = "Login failed."

    async def monitor_otps(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Periodically checks for new OTPs and sends them to Telegram."""
        new_otps = self.scraper.fetch_new_otps()
        if new_otps:
            for otp in new_otps:
                await self.send_message(f"New OTP received: {otp}")
        else:
            logger.info("No new OTPs found.")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sends a message with the current status of the bot."""
        if not await self._check_authorized(update): return
        await update.message.reply_text(f"Current status: {self.bot_status}")

    async def restart_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Restarts the web scraping process."""
        if not await self._check_authorized(update): return

        await update.message.reply_text("Restarting web scraping process...")
        self.bot_status = "Restarting..."
        self.scraper.close() # Close existing driver
        # The start_command will re-initialize the driver and login
        await self.start_command(update, context) 

    async def last_otp_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Retrieves the most recent OTPs."""
        if not await self._check_authorized(update): return

        count = 1
        if context.args:
            try:
                count = int(context.args[0])
                if count <= 0:
                    await update.message.reply_text("Count must be a positive integer.")
                    return
            except ValueError:
                await update.message.reply_text("Please provide a valid number for count (e.g., /last_otp 5).")
                return
        
        await update.message.reply_text(f"Fetching last {count} OTPs...")
        # For now, fetch all and take the last 'count'
        all_otps = self.scraper.fetch_new_otps() # This method currently fetches all visible
        if all_otps:
            last_n_otps = all_otps[-count:]
            for otp in last_n_otps:
                await self.send_message(f"Last OTP: {otp}")
        else:
            await self.send_message("No OTPs found on the page.")

    async def get_old_otps_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Allows fetching historical messages between two dates."""
        if not await self._check_authorized(update): return ConversationHandler.END

        await update.message.reply_text("Please provide the start and end dates in YYYY-MM-DD format (e.g., 2025-10-01 2025-10-19).")
        return DATE_INPUT

    async def receive_dates(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Receives the dates for historical OTPs and fetches them."""
        if not await self._check_authorized(update): return ConversationHandler.END

        date_pattern = r"^\d{4}-\d{2}-\d{2} \d{4}-\d{2}-\d{2}$"
        dates_input = update.message.text.strip()

        if not re.match(date_pattern, dates_input):
            await update.message.reply_text("Invalid date format. Please use YYYY-MM-DD YYYY-MM-DD.")
            return DATE_INPUT # Stay in the same state to ask again

        start_date_str, end_date_str = dates_input.split()

        await update.message.reply_text(f"Fetching historical OTPs from {start_date_str} to {end_date_str}...")
        historical_otps = self.scraper.get_historical_otps(start_date_str, end_date_str)

        if historical_otps:
            for otp in historical_otps:
                await self.send_message(f"Historical OTP: {otp}")
        else:
            await self.send_message(f"No historical OTPs found for the period {start_date_str} to {end_date_str}.")
        
        return ConversationHandler.END

    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Cancels the current conversation."""
        if not await self._check_authorized(update): return ConversationHandler.END
        await update.message.reply_text("Operation cancelled.")
        return ConversationHandler.END

    async def unauthorized_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles messages from unauthorized users."""
        if not await self._check_authorized(update): return
        # For authorized users, just echo for now or ignore
        await update.message.reply_text("I don't understand that command. Use /start, /status, /restart, /last_otp, or /get_old_otps.")

    async def send_message(self, text: str) -> None:
        """Sends a message to the designated Telegram chat ID."""
        try:
            await self.application.bot.send_message(chat_id=self.chat_id, text=text)
        except Exception as e:
            logger.error(f"Failed to send message to Telegram chat {self.chat_id}: {e}")

    def run(self):
        """Starts the bot."""
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    # This block is for testing the bot independently
    # In a real scenario, these would come from environment variables
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID environment variables for testing.")
    else:
        # Placeholder for scraper instance
        class MockScraper:
            notification_callback = None
            def login(self): 
                print("MockScraper: Logging in...")
                if self.notification_callback: self.notification_callback("Mock Login successful.")
                return True
            def handle_popup(self): 
                print("MockScraper: Handling popup...")
                if self.notification_callback: self.notification_callback("Mock Pop-up handled.")
                return False
            def navigate_to_otp_page(self): 
                print("MockScraper: Navigating to OTP page...")
                if self.notification_callback: self.notification_callback("Mock Navigated to OTP page.")
                return True
            def fetch_new_otps(self): 
                print("MockScraper: Fetching new OTPs...")
                return ["Mock OTP 1", "Mock OTP 2"]
            def get_historical_otps(self, start, end): 
                print(f"MockScraper: Fetching historical OTPs from {start} to {end}...")
                return [f"Mock Historical OTP from {start} to {end}"]
            def close(self): 
                print("MockScraper: Closing driver...")
                pass
            def _initialize_driver(self): 
                print("MockScraper: Initializing driver...")
                pass

        mock_scraper = MockScraper()
        bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, mock_scraper)
        print("Starting Telegram bot...")
        bot.run()

