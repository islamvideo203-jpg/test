# Telegram OTP Bot

This project implements a Python-based Telegram bot designed to fetch SMS/OTP messages from the `ivasms.com` website using Selenium for web scraping and forward them to a designated Telegram chat. The bot is intended to be hosted on GitHub Codespaces or a similar environment.

## Features

-   **Automated Login**: Logs into `ivasms.com` using credentials from environment variables.
-   **Pop-up Handling**: Automatically handles optional pop-ups after login.
-   **OTP Page Navigation**: Navigates to the "My SMS Statistics" page.
-   **Continuous Monitoring**: Periodically checks for new SMS messages and sends them to Telegram.
-   **Telegram Commands**:
    -   `/start`: Initiates the bot, logs into `ivasms.com`, and starts monitoring.
    -   `/status`: Reports the current operational status of the bot.
    -   `/restart`: Restarts the web scraping process (logs out, logs in, navigates to OTP page).
    -   `/last_otp [count]`: Fetches the `count` most recent OTPs. Defaults to 1 if `count` is not provided.
    -   `/get_old_otps`: Prompts for a date range (YYYY-MM-DD YYYY-MM-DD) to fetch historical OTPs.
-   **Error Handling**: Provides notifications to Telegram for login failures, navigation issues, and other operational errors.

## Project Structure

```
/telegram-otp-bot
|
|-- /app
|   |-- __init__.py
|   |-- bot.py             # Main Telegram bot logic (command handlers, etc.)
|   |-- scraper.py         # All Selenium web scraping logic
|   |-- config.py          # Configuration (API keys, credentials, URLs)
|   |-- utils.py           # Helper functions
|
|-- requirements.txt       # List of all Python dependencies
|-- main.py                # Entry point to start the bot
|-- .env                   # For storing secrets like credentials and API keys
|-- README.md              # Project documentation
```

## Setup and Installation

### 1. Clone the Repository

```bash
git clone <repository_url>
cd telegram-otp-bot
```

### 2. Environment Variables

Create a `.env` file in the root directory of the project (`/telegram-otp-bot`) and populate it with your credentials and API keys. **Do not commit this file to your version control.**

```ini
TELEGRAM_BOT_TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID="YOUR_TELEGRAM_CHAT_ID"
IVASMS_EMAIL="YOUR_IVASMS_EMAIL"
IVASMS_PASSWORD="YOUR_IVASMS_PASSWORD"
```

-   **`TELEGRAM_BOT_TOKEN`**: Obtain this from BotFather on Telegram. Start a chat with `@BotFather`, send `/newbot`, and follow the instructions.
-   **`TELEGRAM_CHAT_ID`**: This is the ID of the chat where the bot will send messages. You can get this by forwarding a message from your desired chat to `@userinfobot` on Telegram.
-   **`IVASMS_EMAIL`**: Your login email for `ivasms.com`.
-   **`IVASMS_PASSWORD`**: Your login password for `ivasms.com`.

### 3. Install Dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

### 4. Install ChromeDriver

Selenium requires a WebDriver to interact with the browser. For Chrome, you need `chromedriver`. If you are running this in a GitHub Codespaces environment, `chromedriver` is usually pre-installed at `/usr/bin/chromedriver`. If not, you may need to install it manually or adjust the `Service('/usr/bin/chromedriver')` path in `app/scraper.py`.

**For Ubuntu/Debian-based systems (if not in Codespaces):**

```bash
sudo apt update
sudo apt install chromium-chromedriver
```

### 5. Running the Bot

To start the bot, run the `main.py` file:

```bash
python main.py
```

The bot will start, and you should receive an "Bot is online and running." message in your designated Telegram chat. You can then interact with it using the commands listed above.

## Usage

Once the bot is running and you've sent the `/start` command in Telegram:

-   **`/start`**: The bot will attempt to log into `ivasms.com`, handle any pop-ups, and navigate to the SMS statistics page. It will then begin monitoring for new OTPs.
-   **`/status`**: Get an update on the bot's current state (e.g., "Logged in and waiting for OTPs").
-   **`/restart`**: If the bot encounters issues or you want to force a re-login, use this command. It will close the current browser session and start a new one.
-   **`/last_otp [count]`**: To fetch the most recent OTP(s). For example, `/last_otp 3` will send the last 3 messages.
-   **`/get_old_otps`**: Use this to retrieve messages from a specific date range. The bot will prompt you for the start and end dates in `YYYY-MM-DD YYYY-MM-DD` format.

## Error Handling and Notifications

The bot is designed to send detailed error messages to your Telegram chat if any step fails (e.g., login, navigation, element not found). It will also attempt to re-login if the session expires.

## Contributing

Feel free to fork the repository, open issues, or submit pull requests.

## License

This project is open-source and available under the MIT License.

