#!/usr/bin/env python3
"""
Test script to verify Instagram to YouTube automation setup
Optimized for GitHub Codespaces deployment
"""

import os
import sys
import json
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported"""
    print("🔍 Testing package imports...")
    
    try:
        import instaloader
        print("✅ instaloader imported successfully")
    except ImportError as e:
        print(f"❌ instaloader import failed: {e}")
        return False
    
    try:
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        print("✅ Google API packages imported successfully")
    except ImportError as e:
        print(f"❌ Google API packages import failed: {e}")
        return False
    
    try:
        import openai
        print("✅ openai imported successfully")
    except ImportError as e:
        print(f"❌ openai import failed: {e}")
        return False
    
    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, ContextTypes
        print("✅ python-telegram-bot imported successfully")
    except ImportError as e:
        print(f"❌ python-telegram-bot import failed: {e}")
        return False
    
    try:
        import schedule
        print("✅ schedule imported successfully")
    except ImportError as e:
        print(f"❌ schedule import failed: {e}")
        return False
    
    return True

def test_github_secrets():
    """Test if all required GitHub Secrets are configured"""
    print("\n🔍 Testing GitHub Secrets...")
    
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
            # Mask sensitive values
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
        print("Configure these in your repository's Codespaces secrets.")
        return False
    
    return True

def test_youtube_credentials():
    """Test YouTube OAuth2 credentials"""
    print("\n🔍 Testing YouTube credentials...")
    
    # Check if client_secret.json exists
    if Path('client_secret.json').exists():
        print("✅ YouTube client secret file found")
        
        # Validate JSON format
        try:
            with open('client_secret.json', 'r') as f:
                client_secret = json.load(f)
            
            required_keys = ['installed', 'client_id', 'client_secret']
            if all(key in client_secret for key in required_keys):
                print("✅ YouTube client secret format is valid")
                return True
            else:
                print("❌ YouTube client secret missing required keys")
                return False
                
        except json.JSONDecodeError:
            print("❌ YouTube client secret is not valid JSON")
            return False
    else:
        print("❌ YouTube client secret file not found")
        print("Run: python codespaces_setup.py to create it from GitHub Secret")
        return False

def test_telegram_user_id():
    """Test if Telegram user ID is valid"""
    print("\n🔍 Testing Telegram user ID...")
    
    user_id = os.getenv('AUTHORIZED_TELEGRAM_USER_ID')
    if user_id:
        try:
            user_id_int = int(user_id)
            if user_id_int > 0:
                print(f"✅ Valid Telegram user ID: {user_id_int}")
                return True
            else:
                print(f"❌ Invalid Telegram user ID: {user_id_int} (must be positive)")
                return False
        except ValueError:
            print(f"❌ Invalid Telegram user ID format: {user_id}")
            return False
    else:
        print("❌ Telegram user ID not configured")
        return False

def test_codespaces_environment():
    """Test if running in Codespaces"""
    print("\n🔍 Testing Codespaces environment...")
    
    if os.getenv('CODESPACES'):
        print("✅ Running in GitHub Codespaces")
        return True
    else:
        print("⚠️  Not running in Codespaces (some features may not work)")
        return True  # Not a failure, just a warning

def main():
    """Run all tests"""
    print("🚀 Instagram to YouTube Automation - Codespaces Setup Test")
    print("=" * 60)
    
    tests = [
        ("Package Imports", test_imports),
        ("GitHub Secrets", test_github_secrets),
        ("YouTube Credentials", test_youtube_credentials),
        ("Telegram User ID", test_telegram_user_id),
        ("Codespaces Environment", test_codespaces_environment)
    ]
    
    tests_passed = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            tests_passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Your setup is ready to go.")
        print("\nNext steps:")
        print("1. Run: python instagram_youtube_automation.py")
        print("2. Send /start to your Telegram bot")
        print("3. Add target accounts with /add_account username")
        print("4. Test with /run_manual")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nTroubleshooting:")
        print("1. Run: python codespaces_setup.py")
        print("2. Check GitHub Secrets configuration")
        print("3. Verify all API keys are correct")
        sys.exit(1)

if __name__ == "__main__":
    main()