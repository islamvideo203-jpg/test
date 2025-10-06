#!/usr/bin/env python3
"""
Instagram to YouTube Automation Pipeline with Telegram Bot Control
Complete automation script for downloading Instagram Reels and uploading to YouTube
with duplication check, timed scheduling, and Telegram bot control.
Optimized for GitHub Codespaces deployment.
"""

import os
import json
import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import instaloader
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import openai
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import tempfile
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration - Load from environment variables (GitHub Secrets)
INSTA_USERNAME = os.getenv('INSTA_USERNAME', '')
INSTA_PASSWORD = os.getenv('INSTA_PASSWORD', '')
YOUTUBE_CLIENT_SECRET_FILE = os.getenv('YOUTUBE_CLIENT_SECRET_FILE', 'client_secret.json')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
AUTHORIZED_TELEGRAM_USER_ID = int(os.getenv('AUTHORIZED_TELEGRAM_USER_ID', '0'))

# YouTube API configuration
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

# Configuration file path
CONFIG_FILE = 'config.json'

class InstagramYouTubeAutomation:
    def __init__(self):
        self.config = self.load_config()
        self.insta_loader = None
        self.youtube_service = None
        self.openai_client = None
        self.upload_queue = []
        self.setup_services()
        
    def load_config(self) -> Dict:
        """Load configuration from config.json file"""
        default_config = {
            "TARGET_INSTAGRAM_ACCOUNTS": [],
            "POSTED_SHORTCODES": [],
            "last_run": None
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    # Ensure all required keys exist
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return default_config
        else:
            # Create default config file
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict = None):
        """Save configuration to config.json file"""
        if config is None:
            config = self.config
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def setup_services(self):
        """Initialize all required services"""
        try:
            # Setup Instagram loader
            self.insta_loader = instaloader.Instaloader(
                download_pictures=False,
                download_videos=True,
                download_video_thumbnails=False,
                download_geotags=False,
                download_comments=False,
                save_metadata=False,
                compress_json=False
            )
            
            # Login to Instagram
            if INSTA_USERNAME and INSTA_PASSWORD:
                self.insta_loader.login(INSTA_USERNAME, INSTA_PASSWORD)
                logger.info("Instagram login successful")
            
            # Setup YouTube service
            self.setup_youtube_service()
            
            # Setup OpenAI client
            if OPENAI_API_KEY:
                openai.api_key = OPENAI_API_KEY
                self.openai_client = openai
                logger.info("OpenAI client initialized")
            
        except Exception as e:
            logger.error(f"Error setting up services: {e}")
    
    def setup_youtube_service(self):
        """Setup YouTube API service with OAuth2 authentication"""
        try:
            creds = None
            token_file = 'youtube_token.json'
            
            # Load existing credentials
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            
            # If no valid credentials, run OAuth flow
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(YOUTUBE_CLIENT_SECRET_FILE):
                        logger.error(f"YouTube client secret file not found: {YOUTUBE_CLIENT_SECRET_FILE}")
                        return
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        YOUTUBE_CLIENT_SECRET_FILE, SCOPES)
                    # For Codespaces, use a different port and disable local server
                    creds = flow.run_local_server(port=8080, open_browser=False)
                
                # Save credentials for next run
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())
            
            self.youtube_service = build(
                YOUTUBE_API_SERVICE_NAME, 
                YOUTUBE_API_VERSION, 
                credentials=creds
            )
            logger.info("YouTube service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error setting up YouTube service: {e}")
    
    def get_instagram_reels(self, username: str, max_posts: int = 50) -> List[Dict]:
        """Get Instagram Reels from a specific account"""
        try:
            profile = instaloader.Profile.from_username(self.insta_loader.context, username)
            reels = []
            
            for post in profile.get_posts():
                if post.is_video and post.typename == 'GraphVideo':
                    reel_data = {
                        'shortcode': post.shortcode,
                        'caption': post.caption or '',
                        'username': username,
                        'date': post.date,
                        'video_url': post.video_url,
                        'thumbnail_url': post.url
                    }
                    reels.append(reel_data)
                    
                    if len(reels) >= max_posts:
                        break
            
            logger.info(f"Found {len(reels)} reels from @{username}")
            return reels
            
        except Exception as e:
            logger.error(f"Error getting reels from @{username}: {e}")
            return []
    
    def download_reel(self, reel_data: Dict) -> Optional[str]:
        """Download a single Instagram Reel"""
        try:
            # Create temporary directory for downloads
            temp_dir = tempfile.mkdtemp()
            filename = f"{reel_data['shortcode']}.mp4"
            filepath = os.path.join(temp_dir, filename)
            
            # Download the video
            self.insta_loader.download_video(reel_data['video_url'], filepath)
            
            if os.path.exists(filepath):
                logger.info(f"Downloaded reel: {reel_data['shortcode']}")
                return filepath
            else:
                logger.error(f"Failed to download reel: {reel_data['shortcode']}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading reel {reel_data['shortcode']}: {e}")
            return None
    
    def generate_youtube_metadata(self, reel_data: Dict) -> Dict:
        """Generate YouTube metadata using OpenAI API"""
        try:
            if not self.openai_client:
                return self.generate_fallback_metadata(reel_data)
            
            prompt = f"""
            Create optimized YouTube metadata for this Instagram Reel:
            
            Original Caption: {reel_data['caption'][:200]}...
            Creator: @{reel_data['username']}
            
            Generate:
            1. Title (max 70 characters, engaging and clickable)
            2. Description (max 5000 characters, include "Credit to the original creator: @{reel_data['username']}")
            3. Tags (10 relevant tags, comma-separated)
            
            Format as JSON:
            {{
                "title": "Your Title Here",
                "description": "Your description here...\n\nCredit to the original creator: @{reel_data['username']}",
                "tags": ["tag1", "tag2", "tag3", ...]
            }}
            """
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            metadata = json.loads(response.choices[0].message.content)
            logger.info(f"Generated AI metadata for {reel_data['shortcode']}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error generating AI metadata: {e}")
            return self.generate_fallback_metadata(reel_data)
    
    def generate_fallback_metadata(self, reel_data: Dict) -> Dict:
        """Generate fallback metadata without AI"""
        title = f"Instagram Reel by @{reel_data['username']}"
        if len(title) > 70:
            title = title[:67] + "..."
        
        description = f"Credit to the original creator: @{reel_data['username']}\n\n"
        if reel_data['caption']:
            description += f"Original caption: {reel_data['caption'][:1000]}"
        
        tags = [
            "instagram", "reel", "viral", "trending", "short", "video",
            "entertainment", "fun", "creative", "social"
        ]
        
        return {
            "title": title,
            "description": description,
            "tags": tags
        }
    
    def upload_to_youtube(self, file_path: str, metadata: Dict, shortcode: str) -> bool:
        """Upload video to YouTube"""
        try:
            if not self.youtube_service:
                logger.error("YouTube service not initialized")
                return False
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': metadata['title'],
                    'description': metadata['description'],
                    'tags': metadata['tags'],
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': 'unlisted'
                }
            }
            
            # Create media upload
            media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
            
            # Execute upload
            insert_request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            # Execute the upload
            response = insert_request.execute()
            
            if 'id' in response:
                video_id = response['id']
                logger.info(f"Successfully uploaded {shortcode} as YouTube video: {video_id}")
                
                # Add shortcode to posted list
                self.config['POSTED_SHORTCODES'].append(shortcode)
                self.save_config()
                
                # Delete the local file
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted local file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")
                
                return True
            else:
                logger.error(f"Upload failed for {shortcode}")
                return False
                
        except Exception as e:
            logger.error(f"Error uploading {shortcode} to YouTube: {e}")
            return False
    
    def run_automation(self) -> Dict:
        """Main automation function - download and prepare videos for upload"""
        logger.info("Starting daily automation process")
        results = {
            'videos_selected': 0,
            'duplicates_skipped': 0,
            'old_videos_used': 0,
            'errors': []
        }
        
        try:
            selected_videos = []
            target_count = 3
            
            # Get reels from all target accounts
            all_reels = []
            for username in self.config['TARGET_INSTAGRAM_ACCOUNTS']:
                reels = self.get_instagram_reels(username, max_posts=20)
                all_reels.extend(reels)
            
            # Sort by date (newest first)
            all_reels.sort(key=lambda x: x['date'], reverse=True)
            
            # Select videos with duplication check
            for reel in all_reels:
                if len(selected_videos) >= target_count:
                    break
                
                # Check for duplicates
                if reel['shortcode'] in self.config['POSTED_SHORTCODES']:
                    results['duplicates_skipped'] += 1
                    continue
                
                # Download the reel
                file_path = self.download_reel(reel)
                if file_path:
                    # Generate metadata
                    metadata = self.generate_youtube_metadata(reel)
                    
                    # Add to selected videos
                    selected_videos.append({
                        'file_path': file_path,
                        'metadata': metadata,
                        'shortcode': reel['shortcode'],
                        'username': reel['username']
                    })
                    results['videos_selected'] += 1
                else:
                    results['errors'].append(f"Failed to download {reel['shortcode']}")
            
            # If we don't have enough new videos, try older content
            if len(selected_videos) < target_count:
                logger.info("Not enough new content, checking older reels...")
                for reel in all_reels:
                    if len(selected_videos) >= target_count:
                        break
                    
                    if reel['shortcode'] in self.config['POSTED_SHORTCODES']:
                        continue
                    
                    # Skip if already selected
                    if any(v['shortcode'] == reel['shortcode'] for v in selected_videos):
                        continue
                    
                    file_path = self.download_reel(reel)
                    if file_path:
                        metadata = self.generate_youtube_metadata(reel)
                        selected_videos.append({
                            'file_path': file_path,
                            'metadata': metadata,
                            'shortcode': reel['shortcode'],
                            'username': reel['username']
                        })
                        results['old_videos_used'] += 1
                        results['videos_selected'] += 1
            
            # Schedule uploads
            if selected_videos:
                self.schedule_uploads(selected_videos)
                logger.info(f"Scheduled {len(selected_videos)} videos for upload")
            
            # Update last run time
            self.config['last_run'] = datetime.now().isoformat()
            self.save_config()
            
        except Exception as e:
            logger.error(f"Error in automation process: {e}")
            results['errors'].append(str(e))
        
        return results
    
    def schedule_uploads(self, videos: List[Dict]):
        """Schedule video uploads at specific times"""
        upload_times = ['06:00', '12:00', '17:00']
        
        for i, video in enumerate(videos):
            if i < len(upload_times):
                time_str = upload_times[i]
                schedule.every().day.at(time_str).do(
                    self.upload_scheduled_video, 
                    video['file_path'], 
                    video['metadata'], 
                    video['shortcode']
                )
                logger.info(f"Scheduled {video['shortcode']} for upload at {time_str}")
    
    def upload_scheduled_video(self, file_path: str, metadata: Dict, shortcode: str):
        """Upload a scheduled video"""
        logger.info(f"Uploading scheduled video: {shortcode}")
        success = self.upload_to_youtube(file_path, metadata, shortcode)
        
        if success:
            logger.info(f"Successfully uploaded scheduled video: {shortcode}")
        else:
            logger.error(f"Failed to upload scheduled video: {shortcode}")

# Telegram Bot Functions
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    if update.effective_user.id != AUTHORIZED_TELEGRAM_USER_ID:
        await update.message.reply_text("Unauthorized access.")
        return
    
    await update.message.reply_text(
        "🤖 Instagram to YouTube Automation Bot is running!\n\n"
        "Available commands:\n"
        "/run_manual - Run content preparation now\n"
        "/list_accounts - Show target accounts\n"
        "/add_account [username] - Add new target\n"
        "/edit_metadata [video_id] [new_title] - Edit video metadata\n"
        "/status - Check schedule status\n"
        "/check_duplicates - Check posted count"
    )

async def run_manual_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /run_manual command"""
    if update.effective_user.id != AUTHORIZED_TELEGRAM_USER_ID:
        await update.message.reply_text("Unauthorized access.")
        return
    
    await update.message.reply_text("🔄 Running manual automation...")
    
    try:
        results = automation.run_automation()
        
        message = f"✅ Automation completed!\n\n"
        message += f"📹 Videos selected: {results['videos_selected']}\n"
        message += f"🚫 Duplicates skipped: {results['duplicates_skipped']}\n"
        message += f"📚 Old videos used: {results['old_videos_used']}\n"
        
        if results['errors']:
            message += f"\n❌ Errors: {len(results['errors'])}\n"
            for error in results['errors'][:3]:  # Show first 3 errors
                message += f"• {error}\n"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error running automation: {str(e)}")

async def list_accounts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /list_accounts command"""
    if update.effective_user.id != AUTHORIZED_TELEGRAM_USER_ID:
        await update.message.reply_text("Unauthorized access.")
        return
    
    accounts = automation.config.get('TARGET_INSTAGRAM_ACCOUNTS', [])
    
    if accounts:
        message = "📋 Target Instagram Accounts:\n\n"
        for i, account in enumerate(accounts, 1):
            message += f"{i}. @{account}\n"
    else:
        message = "📋 No target accounts configured."
    
    await update.message.reply_text(message)

async def add_account_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /add_account command"""
    if update.effective_user.id != AUTHORIZED_TELEGRAM_USER_ID:
        await update.message.reply_text("Unauthorized access.")
        return
    
    if not context.args:
        await update.message.reply_text("Usage: /add_account [username]")
        return
    
    username = context.args[0].lstrip('@')
    
    if username in automation.config['TARGET_INSTAGRAM_ACCOUNTS']:
        await update.message.reply_text(f"@{username} is already in the target list.")
        return
    
    automation.config['TARGET_INSTAGRAM_ACCOUNTS'].append(username)
    automation.save_config()
    
    await update.message.reply_text(f"✅ Added @{username} to target accounts.")

async def edit_metadata_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /edit_metadata command"""
    if update.effective_user.id != AUTHORIZED_TELEGRAM_USER_ID:
        await update.message.reply_text("Unauthorized access.")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /edit_metadata [video_id] [new_title]")
        return
    
    video_id = context.args[0]
    new_title = ' '.join(context.args[1:])
    
    try:
        if not automation.youtube_service:
            await update.message.reply_text("❌ YouTube service not available.")
            return
        
        # Get current video details
        video_response = automation.youtube_service.videos().list(
            part='snippet',
            id=video_id
        ).execute()
        
        if not video_response['items']:
            await update.message.reply_text("❌ Video not found.")
            return
        
        # Update video metadata
        video = video_response['items'][0]
        video['snippet']['title'] = new_title
        
        update_response = automation.youtube_service.videos().update(
            part='snippet',
            body=video
        ).execute()
        
        await update.message.reply_text(f"✅ Updated video title to: {new_title}")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error updating metadata: {str(e)}")

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    if update.effective_user.id != AUTHORIZED_TELEGRAM_USER_ID:
        await update.message.reply_text("Unauthorized access.")
        return
    
    last_run = automation.config.get('last_run', 'Never')
    message = f"📊 Automation Status\n\n"
    message += f"🕐 Last run: {last_run}\n"
    message += f"📅 Next uploads:\n"
    message += f"• 6:00 AM\n"
    message += f"• 12:00 PM\n"
    message += f"• 5:00 PM\n"
    message += f"📹 Target accounts: {len(automation.config.get('TARGET_INSTAGRAM_ACCOUNTS', []))}"
    
    await update.message.reply_text(message)

async def check_duplicates_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /check_duplicates command"""
    if update.effective_user.id != AUTHORIZED_TELEGRAM_USER_ID:
        await update.message.reply_text("Unauthorized access.")
        return
    
    posted_count = len(automation.config.get('POSTED_SHORTCODES', []))
    await update.message.reply_text(f"📊 Posted shortcodes count: {posted_count}")

def setup_telegram_bot():
    """Setup and configure Telegram bot"""
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Telegram bot token not provided")
        return None
    
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("run_manual", run_manual_command))
    application.add_handler(CommandHandler("list_accounts", list_accounts_command))
    application.add_handler(CommandHandler("add_account", add_account_command))
    application.add_handler(CommandHandler("edit_metadata", edit_metadata_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("check_duplicates", check_duplicates_command))
    
    return application

def run_scheduler():
    """Run the scheduler in a separate thread"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def main():
    """Main function to run the automation"""
    global automation
    
    # Initialize automation
    automation = InstagramYouTubeAutomation()
    
    # Setup Telegram bot
    bot_application = setup_telegram_bot()
    if not bot_application:
        logger.error("Failed to setup Telegram bot")
        return
    
    # Schedule daily automation at 10 PM
    schedule.every().day.at("22:00").do(automation.run_automation)
    
    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Starting Instagram to YouTube automation...")
    logger.info("Telegram bot is running...")
    logger.info("Daily automation scheduled for 10:00 PM")
    logger.info("Upload times: 6:00 AM, 12:00 PM, 5:00 PM")
    
    # Run Telegram bot
    try:
        bot_application.run_polling()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error running bot: {e}")

if __name__ == "__main__":
    main()