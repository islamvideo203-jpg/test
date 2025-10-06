#!/usr/bin/env python3
"""
GitHub Codespaces Setup Script for Instagram to YouTube Automation
Automatically configures the environment and sets up the automation
"""

import os
import json
import subprocess
import sys
from pathlib import Path

def check_github_secrets():
    """Check if all required GitHub Secrets are configured"""
    print("🔍 Checking GitHub Secrets configuration...")
    
    required_secrets = [
        'INSTA_USERNAME',
        'INSTA_PASSWORD', 
        'YOUTUBE_CLIENT_SECRET',
        'OPENAI_API_KEY',
        'TELEGRAM_BOT_TOKEN',
        'AUTHORIZED_TELEGRAM_USER_ID'
    ]
    
    missing_secrets = []
    
    for secret in required_secrets:
        value = os.getenv(secret)
        if value:
            if 'PASSWORD' in secret or 'TOKEN' in secret or 'KEY' in secret:
                masked_value = value[:4] + '*' * (len(value) - 4)
                print(f"✅ {secret}: {masked_value}")
            else:
                print(f"✅ {secret}: {value}")
        else:
            print(f"❌ {secret}: Not configured")
            missing_secrets.append(secret)
    
    if missing_secrets:
        print(f"\n❌ Missing secrets: {', '.join(missing_secrets)}")
        print("Please configure these in your repository's Codespaces secrets.")
        return False
    
    return True

def setup_youtube_credentials():
    """Setup YouTube OAuth2 credentials from GitHub Secret"""
    print("\n🔧 Setting up YouTube credentials...")
    
    youtube_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
    if not youtube_secret:
        print("❌ YOUTUBE_CLIENT_SECRET not found")
        return False
    
    try:
        # Parse the JSON secret
        client_secret = json.loads(youtube_secret)
        
        # Save to file
        with open('client_secret.json', 'w') as f:
            json.dump(client_secret, f, indent=2)
        
        print("✅ YouTube client secret configured")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in YOUTUBE_CLIENT_SECRET: {e}")
        return False
    except Exception as e:
        print(f"❌ Error setting up YouTube credentials: {e}")
        return False

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False

def test_setup():
    """Test the complete setup"""
    print("\n🧪 Testing setup...")
    
    try:
        # Test imports
        import instaloader
        from googleapiclient.discovery import build
        import openai
        from telegram import Update
        import schedule
        print("✅ All packages imported successfully")
        
        # Test environment variables
        if not check_github_secrets():
            return False
        
        # Test YouTube credentials
        if not setup_youtube_credentials():
            return False
        
        print("✅ Setup test completed successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False

def create_config_file():
    """Create initial configuration file"""
    print("\n📝 Creating configuration file...")
    
    config = {
        "TARGET_INSTAGRAM_ACCOUNTS": [],
        "POSTED_SHORTCODES": [],
        "last_run": None
    }
    
    try:
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=2)
        print("✅ Configuration file created")
        return True
    except Exception as e:
        print(f"❌ Error creating config file: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 GitHub Codespaces Setup for Instagram to YouTube Automation")
    print("=" * 60)
    
    # Check if we're in Codespaces
    if not os.getenv('CODESPACES'):
        print("⚠️  This script is designed for GitHub Codespaces")
        print("   Some features may not work in other environments")
    
    steps = [
        ("Checking GitHub Secrets", check_github_secrets),
        ("Installing Dependencies", install_dependencies),
        ("Setting up YouTube Credentials", setup_youtube_credentials),
        ("Creating Configuration", create_config_file),
        ("Testing Setup", test_setup)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n{'='*20} {step_name} {'='*20}")
        if step_func():
            success_count += 1
        else:
            print(f"❌ {step_name} failed")
            break
    
    print("\n" + "=" * 60)
    print(f"📊 Setup Results: {success_count}/{len(steps)} steps completed")
    
    if success_count == len(steps):
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python instagram_youtube_automation.py")
        print("2. Send /start to your Telegram bot")
        print("3. Add target accounts with /add_account username")
        print("4. Test with /run_manual")
    else:
        print("❌ Setup failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Verify all GitHub Secrets are configured")
        print("2. Check that YouTube client secret is valid JSON")
        print("3. Ensure all API keys are correct")
        sys.exit(1)

if __name__ == "__main__":
    main()
