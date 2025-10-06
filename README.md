# Instagram to YouTube Automation Pipeline

A complete Python automation script that downloads Instagram Reels and uploads them to YouTube with Telegram bot control, duplication checking, and timed scheduling. **Optimized for GitHub Codespaces deployment.**

## 🌟 Features

- 🤖 **Telegram Bot Control**: Full control via Telegram commands
- 🔄 **Duplication Check**: Prevents re-uploading the same content
- ⏰ **Timed Scheduling**: Automatic daily content preparation and scheduled uploads
- 🎯 **Smart Content Selection**: Prioritizes new content with fallback to older content
- 🤖 **AI-Powered Metadata**: OpenAI-generated YouTube titles, descriptions, and tags
- 📊 **Progress Tracking**: Real-time status updates and error reporting
- 🔐 **Secure Authentication**: OAuth2 for YouTube, secure credential management
- ☁️ **Codespaces Ready**: Optimized for GitHub Codespaces deployment

## 🚀 Quick Start with GitHub Codespaces

### Option 1: One-Click Setup

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?repo=YOUR_USERNAME/YOUR_REPO_NAME)

### Option 2: Manual Setup

1. **Fork this repository**
2. **Open in Codespaces**:
   - Click "Code" → "Codespaces" → "Create codespace on main"
3. **Configure GitHub Secrets**:
   - Go to repository settings → "Secrets and variables" → "Codespaces"
   - Add the required secrets (see below)
4. **Run setup**:
   ```bash
   python codespaces_setup.py
   python test_setup.py
   python instagram_youtube_automation.py
   ```

## 🔧 GitHub Secrets Configuration

Configure these secrets in your repository's Codespaces settings:

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `INSTA_USERNAME` | Your Instagram username | `your_username` |
| `INSTA_PASSWORD` | Your Instagram password | `your_password` |
| `YOUTUBE_CLIENT_SECRET` | YouTube OAuth2 JSON content | `{"installed":{"client_id":"..."}}` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-your-key-here` |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | `123456789:ABC...` |
| `AUTHORIZED_TELEGRAM_USER_ID` | Your Telegram user ID | `123456789` |

## 📋 Prerequisites

### Required Accounts & Services
- **Instagram Account** (for scraping content)
- **YouTube Channel** (for uploading videos)
- **Google Cloud Project** (for YouTube API)
- **OpenAI Account** (for AI metadata generation)
- **Telegram Account** (for bot control)

### YouTube API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable YouTube Data API v3
4. Create OAuth2 credentials (Desktop application)
5. Copy the JSON content to `YOUTUBE_CLIENT_SECRET` secret

### Telegram Bot Setup
1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Get your user ID with @userinfobot

## 🕐 Upload Schedule

- **Content Preparation**: Daily at 10:00 PM
- **Video 1 Upload**: 6:00 AM
- **Video 2 Upload**: 12:00 PM (Noon)
- **Video 3 Upload**: 5:00 PM

## 🤖 Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Greet the user and show available commands |
| `/run_manual` | Run content preparation immediately |
| `/list_accounts` | Show current target Instagram accounts |
| `/add_account [username]` | Add new target account |
| `/edit_metadata [video_id] [new_title]` | Edit YouTube video metadata |
| `/status` | Check automation status and schedule |
| `/check_duplicates` | Show count of posted shortcodes |

## 📁 Project Structure

```
instagram_youtube_automation.py  # Main automation script
codespaces_setup.py             # Codespaces setup script
test_setup.py                   # Setup verification
requirements.txt                # Python dependencies
config.json                     # Runtime configuration (auto-created)
client_secret.json              # YouTube OAuth credentials (auto-created)
youtube_token.json              # YouTube OAuth token (auto-created)
automation.log                  # Application logs
.github/codespaces/README.md    # Codespaces documentation
```

## 🔒 Security & Best Practices

- **GitHub Secrets**: All sensitive data stored securely
- **OAuth2 Flow**: Secure YouTube authentication
- **User Authorization**: Telegram user ID verification
- **Error Logging**: Comprehensive error tracking
- **File Cleanup**: Automatic temporary file removal
- **Codespaces Isolation**: Secure, isolated environment

## 🛠️ Troubleshooting

### Common Issues in Codespaces:

1. **"GitHub Secrets not found"**:
   - Verify secrets are configured in repository settings
   - Check secret names match exactly
   - Ensure secrets are enabled for Codespaces

2. **"YouTube OAuth2 failed"**:
   - Verify `YOUTUBE_CLIENT_SECRET` is valid JSON
   - Check port 8080 is forwarded
   - Complete OAuth flow in browser

3. **"Instagram login failed"**:
   - Check credentials in GitHub Secrets
   - Try manual login first
   - Disable 2FA temporarily if enabled

4. **"Telegram bot not responding"**:
   - Verify bot token and user ID
   - Check bot is not blocked
   - Ensure bot is running

### Debug Commands:

```bash
# Check setup
python test_setup.py

# View logs
tail -f automation.log

# Manual setup
python codespaces_setup.py
```

## 🚀 Deployment Options

### GitHub Codespaces (Recommended)
- ✅ Easy setup and management
- ✅ Secure credential storage
- ✅ Automatic environment configuration
- ✅ Persistent storage
- ✅ No local installation required

### Local Development
- Clone repository
- Install dependencies: `pip install -r requirements.txt`
- Create `.env` file with credentials
- Run: `python instagram_youtube_automation.py`

### Cloud VPS
- Deploy to any cloud provider
- Use environment variables for credentials
- Set up process management (systemd, PM2, etc.)

## 📊 Monitoring & Maintenance

- **Logs**: Check `automation.log` for detailed information
- **Status**: Use `/status` command in Telegram
- **Errors**: Bot sends notifications for critical failures
- **Updates**: Monitor repository for updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is provided as-is for educational and personal use. Please respect Instagram's and YouTube's terms of service.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs in `automation.log`
3. Test setup with `python test_setup.py`
4. Open an issue on GitHub

---

**Ready to automate your content pipeline?** 🚀

[Open in Codespaces](https://github.com/codespaces/new) and start automating your Instagram to YouTube workflow today!