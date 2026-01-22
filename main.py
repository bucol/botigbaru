#!/usr/bin/env python3
"""
Instagram Bot - Main Controller
Mengintegrasikan semua module menjadi satu sistem
"""

import os
import sys
import signal
import asyncio
import logging
import random
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Setup path agar module bisa ditemukan
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

# Load environment variables
load_dotenv()

# --- IMPORT CORE MODULES ---
from core.device_identity_generator import DeviceIdentityGenerator
# Fallback untuk VerificationHandler agar tidak error jika file belum sempurna
try:
    from core.verification_handler import VerificationHandler
except ImportError:
    class VerificationHandler:
        def __init__(self):
            self.max_retries = 3

from core.login_manager import LoginManager
from core.analytics import Analytics
from core.scheduler import MultiAccountScheduler
from core.telegram_handler import TelegramBotHandler as TelegramHandler

# --- IMPORT FEATURE MODULES ---
from features.auto_like import AutoLike
from features.auto_follow import AutoFollow
from features.auto_comment import AutoComment
from features.auto_story import AutoStory
from features.auto_dm import AutoDM
from features.target_scraper import TargetScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BotController:
    """Main controller yang mengintegrasikan semua module"""
    
    def __init__(self):
        self.running = False
        self.paused = False
        
        # Ensure directories exist
        for folder in ['data', 'data/scraped', 'logs', 'sessions']:
            Path(folder).mkdir(parents=True, exist_ok=True)
        
        # Initialize core modules
        self.login_manager = LoginManager()
        self.verification_handler = VerificationHandler()
        self.analytics = Analytics()
        self.scheduler = MultiAccountScheduler()
        
        # Initialize feature modules (will be set after login)
        self.auto_like = None
        self.auto_follow = None
        self.auto_comment = None
        self.auto_story = None
        self.auto_dm = None
        self.scraper = None
        
        # Telegram handler
        self.telegram = None
        
        # Current active client
        self.current_client = None
        self.current_account = None
        
        # Stats
        self.start_time = None
        self.actions_count = {
            'likes': 0,
            'follows': 0,
            'comments': 0,
            'stories': 0,
            'dms': 0
        }
        
    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers"""
        try:
            signal.signal(signal.SIGINT, self.shutdown)
            signal.signal(signal.SIGTERM, self.shutdown)
        except ValueError:
            # Handle case if running in non-main thread (rare but possible)
            logger.warning("Could not setup signal handlers (likely running in background thread)")
        
    def shutdown(self, signum=None, frame=None):
        """Graceful shutdown"""
        logger.info("🛑 Shutting down bot...")
        self.running = False
        
        # Save analytics
        if self.analytics:
            try:
                self.analytics.save_stats()
            except Exception as e:
                logger.error(f"Error saving stats: {e}")
            
        # Logout current session
        if self.current_client:
            try:
                self.login_manager.logout(self.current_account)
            except:
                pass
                
        logger.info("✅ Bot stopped gracefully")
        sys.exit(0)
        
    def initialize_features(self, client):
        """Initialize feature modules dengan client"""
        self.current_client = client
        self.auto_like = AutoLike(client)
        self.auto_follow = AutoFollow(client)
        self.auto_comment = AutoComment(client)
        self.auto_story = AutoStory(client)
        self.auto_dm = AutoDM(client)
        self.scraper = TargetScraper(client)
        
    def login_account(self, username: str = None) -> bool:
        """Login ke akun Instagram"""
        try:
            accounts = self.login_manager.get_accounts()
            
            if not accounts:
                logger.error("❌ Tidak ada akun tersimpan!")
                return False
                
            if username:
                account = next((a for a in accounts if a['username'] == username), None)
                if not account:
                    logger.error(f"❌ Akun {username} tidak ditemukan!")
                    return False
            else:
                # Use first active account
                account = next((a for a in accounts if a.get('is_active', True)), accounts[0])
                
            logger.info(f"🔐 Login ke @{account['username']}...")
            
            # Disini nanti kita pastikan device ID di-generate biar unik (Anti-Detect)
            client = self.login_manager.login(
                account['username'],
                account['password']
            )
            
            if client:
                self.current_account = account['username']
                self.initialize_features(client)
                self.analytics.track_action('login', account['username'])
                logger.info(f"✅ Berhasil login ke @{account['username']}")
                return True
            else:
                logger.error(f"❌ Gagal login ke @{account['username']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False
            
    def rotate_account(self) -> bool:
        """Rotasi ke akun berikutnya"""
        try:
            accounts = self.login_manager.get_accounts()
            active_accounts = [a for a in accounts if a.get('is_active', True)]
            
            if len(active_accounts) < 2:
                logger.warning("⚠️ Tidak cukup akun untuk rotasi.")
                return False
                
            # Find next account
            current_idx = next(
                (i for i, a in enumerate(active_accounts) 
                 if a['username'] == self.current_account), 
                -1
            )
            next_idx = (current_idx + 1) % len(active_accounts)
            next_account = active_accounts[next_idx]
            
            logger.info(f"🔄 Rotating account: @{self.current_account} -> @{next_account['username']}")

            # Logout current
            if self.current_client:
                try:
                    self.login_manager.logout(self.current_account)
                except Exception as e:
                    logger.warning(f"Logout error: {e}")
                
            # Login next
            return self.login_account(next_account['username'])
            
        except Exception as e:
            logger.error(f"❌ Rotate error: {e}")
            return False
            
    async def run_auto_actions(self):
        """Jalankan auto actions berdasarkan schedule"""
        while self.running:
            if self.paused:
                await asyncio.sleep(5)
                continue
                
            try:
                # Check scheduler for pending tasks
                next_task = self.scheduler.get_next_task()
                
                if next_task:
                    action_type = next_task.get('action')
                    target = next_task.get('target')
                    
                    logger.info(f"▶️ Executing: {action_type} -> {target}")
                    
                    result = {}
                    
                    if action_type == 'like':
                        result = self.auto_like.like_by_hashtag(target, limit=random.randint(3, 7)) # Random limit
                        self.actions_count['likes'] += result.get('liked', 0)
                        
                    elif action_type == 'follow':
                        result = self.auto_follow.follow_user_followers(target, limit=random.randint(3, 8))
                        self.actions_count['follows'] += result.get('followed', 0)
                        
                    elif action_type == 'comment':
                        result = self.auto_comment.comment_by_hashtag(target, limit=random.randint(2, 5))
                        self.actions_count['comments'] += result.get('commented', 0)
                        
                    elif action_type == 'story':
                        result = self.auto_story.view_followers_stories(limit=random.randint(8, 15))
                        self.actions_count['stories'] += result.get('viewed', 0)
                        
                    elif action_type == 'dm':
                        result = self.auto_dm.send_welcome_dm(target)
                        if result.get('success'):
                            self.actions_count['dms'] += 1
                            
                    # Track analytics
                    self.analytics.track_action(action_type, target, result)
                    
                    # Mark task completed
                    self.scheduler.complete_task(next_task['id'])
                    
                # --- LOGIKA ANTI-DETECT (HUMAN BEHAVIOR) ---
                # Jangan pakai waktu statis, pakai range yang lebar dan acak
                delay = random.uniform(45, 120) 
                logger.info(f"⏳ Sleeping for {int(delay)}s (Human behavior)...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ Auto action error: {e}")
                await asyncio.sleep(60)
                
    async def run_telegram_bot(self):
        """Jalankan Telegram bot handler"""
        try:
            self.telegram = TelegramHandler(self)
            await self.telegram.start()
        except Exception as e:
            logger.error(f"❌ Telegram bot error: {e}")
            
    def get_status(self) -> dict:
        """Get current bot status"""
        uptime = None
        if self.start_time:
            uptime = str(datetime.now() - self.start_time).split('.')[0]
            
        return {
            'running': self.running,
            'paused': self.paused,
            'current_account': self.current_account,
            'uptime': uptime,
            'actions': self.actions_count,
            'stats': self.analytics.get_today_stats()
        }
        
    def pause(self):
        """Pause bot actions"""
        self.paused = True
        logger.info("⏸️ Bot paused")
        
    def resume(self):
        """Resume bot actions"""
        self.paused = False
        logger.info("▶️ Bot resumed")
        
    async def start(self):
        """Start the bot"""
        logger.info("🚀 Starting Instagram Bot...")
        
        self.setup_signal_handlers()
        self.running = True
        self.start_time = datetime.now()
        
        # Login to first account
        if not self.login_account():
            logger.error("❌ Failed to login initial account. Waiting for commands or manual login...")
            # Kita tidak return, agar bot tetap jalan (misal nunggu perintah Telegram)
            
        # Run tasks concurrently
        await asyncio.gather(
            self.run_auto_actions(),
            self.run_telegram_bot()
        )

def main():
    """Entry point"""
    print("""
    ╔══════════════════════════════════════╗
    ║      Instagram Bot v2.0              ║
    ║      Multi-Account Automation        ║
    ╚══════════════════════════════════════╝
    """)
    
    controller = BotController()
    
    try:
        if sys.platform == 'win32':
            # Fix untuk Windows Event Loop jika diperlukan
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(controller.start())
    except KeyboardInterrupt:
        controller.shutdown()
    except Exception as e:
        logger.critical(f"🔥 Critical Error: {e}")

if __name__ == "__main__":
    main()