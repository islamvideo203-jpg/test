# Instagram to YouTube Automation - GitHub Codespaces Setup

This repository is configured to run the Instagram to YouTube automation pipeline in GitHub Codespaces.

## 🚀 Quick Start in Codespaces

### 1. Open in Codespaces
- Click the "Code" button on this repository
- Select "Codespaces" tab
- Click "Create codespace on main"

### 2. Configure Secrets
Before running the automation, you need to set up GitHub Secrets:

1. Go to your repository settings
2. Navigate to "Secrets and variables" → "Codespaces"
3. Add the following secrets:

```
INSTA_USERNAME - Your Instagram username
INSTA_PASSWORD - Your Instagram password
YOUTUBE_CLIENT_SECRET - Your YouTube OAuth2 client secret JSON content
OPENAI_API_KEY - Your OpenAI API key
TELEGRAM_BOT_TOKEN - Your Telegram bot token
AUTHORIZED_TELEGRAM_USER_ID - Your Telegram user ID
```

### 3. Run the Setup
Once in Codespaces, run:

```bash
# Install dependencies
pip install -r requirements.txt

# Test your setup
python test_setup.py

# Start the automation
python instagram_youtube_automation.py
```

## 🔧 Codespaces-Specific Features

### Automatic Environment Setup
- Environment variables are automatically loaded from GitHub Secrets
- No need to create `.env` files manually
- Secure credential management through GitHub

### Port Configuration
- YouTube OAuth2 flow uses port 8080 (Codespaces compatible)
- Automatic port forwarding for OAuth authentication

### Persistent Storage
- Configuration and tokens are stored in the Codespaces environment
- Data persists between Codespaces sessions

## 📋 Setup Checklist

- [ ] Repository forked/cloned
- [ ] Codespace created
- [ ] GitHub Secrets configured
- [ ] Dependencies installed
- [ ] Setup test passed
- [ ] Automation running

## 🛠️ Troubleshooting

### Common Issues in Codespaces:

1. **OAuth2 Flow Issues**:
   - Make sure port 8080 is forwarded
   - Check that YouTube client secret is properly formatted JSON

2. **Instagram Login Issues**:
   - Verify credentials in GitHub Secrets
   - Try manual login first

3. **Telegram Bot Not Responding**:
   - Check bot token and user ID in secrets
   - Ensure bot is not blocked

## 🔒 Security Notes

- All sensitive data is stored in GitHub Secrets
- No credentials are stored in the repository
- OAuth tokens are automatically managed
- Codespaces provides secure, isolated environment

## 📊 Monitoring

- Check logs in the terminal output
- Use Telegram bot commands to monitor status
- View automation.log for detailed logs

## 🎯 Next Steps

1. Configure your target Instagram accounts via Telegram
2. Test with `/run_manual` command
3. Monitor the daily automation schedule
4. Check your YouTube channel for uploaded videos
