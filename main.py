#!/usr/bin/env python3
"""
Instagram Bot - Main Controller (Windows Fix)
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

# --- FIX 1: FORCE UTF-8 FOR WINDOWS CONSOLE ---
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

load_dotenv()

# --- IMPORT CORE ---
from core.device_identity_generator import DeviceIdentityGenerator
try:
    from core.verification_handler import VerificationHandler
except ImportError:
    class VerificationHandler:
        def __init__(self): self.max_retries = 3

from core.login_manager import LoginManager
from core.analytics import Analytics
from core.scheduler import MultiAccountScheduler

# --- IMPORT FEATURES ---
from features.auto_like import AutoLike
from features.auto_follow import AutoFollow
from features.auto_comment import AutoComment
from features.auto_story import AutoStory
from features.auto_dm import AutoDM
from features.target_scraper import TargetScraper

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout) # Use stdout with utf-8 fix
    ]
)
logger = logging.getLogger(__name__)

class BotController:
    def __init__(self):
        self.running = False
        self.paused = False
        
        for folder in ['data', 'data/scraped', 'logs', 'sessions']:
            Path(folder).mkdir(parents=True, exist_ok=True)
        
        self.login_manager = LoginManager()
        self.analytics = Analytics()
        self.scheduler = MultiAccountScheduler()
        
        # Modules placeholder
        self.auto_like = None
        self.auto_follow = None
        self.auto_comment = None
        self.auto_story = None
        self.auto_dm = None
        self.scraper = None
        
        self.current_client = None
        self.current_account = None
        
        self.start_time = None
        self.actions_count = {'likes': 0, 'follows': 0, 'comments': 0, 'stories': 0, 'dms': 0}

    def setup_signal_handlers(self):
        try:
            signal.signal(signal.SIGINT, self.shutdown)
            signal.signal(signal.SIGTERM, self.shutdown)
        except: pass

    def shutdown(self, signum=None, frame=None):
        logger.info("🛑 Shutting down bot...")
        self.running = False
        if self.analytics: self.analytics.save_stats()
        sys.exit(0)

    def initialize_features(self, client):
        self.current_client = client
        self.auto_like = AutoLike(client, self.analytics)
        self.auto_follow = AutoFollow(client, self.analytics)
        self.auto_comment = AutoComment(client, self.analytics)
        self.auto_story = AutoStory(client)
        self.auto_dm = AutoDM(client)
        self.scraper = TargetScraper(client)

    def login_account(self, username: str = None) -> bool:
        try:
            # FIX 2: method get_accounts() sudah ada di LoginManager sekarang
            accounts = self.login_manager.get_accounts()
            
            if not accounts:
                logger.error("❌ Tidak ada akun tersimpan! Jalankan setup_wizard.py dulu.")
                return False
                
            if username:
                account = next((a for a in accounts if a['username'] == username), None)
            else:
                account = next((a for a in accounts if a.get('is_active', True)), accounts[0])
            
            if not account: return False

            logger.info(f"🔐 Login ke @{account['username']}...")
            client = self.login_manager.login(account['username'], account['password'])
            
            if client:
                self.current_account = account['username']
                self.initialize_features(client)
                self.analytics.track_action('login', True, {'username': account['username']})
                
                # --- MENJADWALKAN TUGAS OTOMATIS ---
                logger.info("📅 Scheduling tasks...")
                
                # 1. Auto Story (Jalan tiap 30-45 menit)
                self.scheduler.register_task(
                    account['username'], "auto_story", 
                    lambda: self.auto_story.view_following_stories(limit=random.randint(10, 20)),
                    base_interval=30
                )
                
                # 2. Auto Like (Jalan tiap 45-60 menit)
                self.scheduler.register_task(
                    account['username'], "auto_like",
                    lambda: self.auto_like.like_by_hashtag("fyp", limit=random.randint(3, 7)),
                    base_interval=45
                )

                return True
            else:
                return False
        except Exception as e:
            logger.error(f"❌ Login Error: {e}")
            return False

    async def run_auto_actions(self):
        """Loop utama untuk menjalankan scheduler"""
        logger.info("🤖 Bot Engine Started.")
        while self.running:
            if self.paused:
                await asyncio.sleep(5)
                continue
            
            # Ambil task dari scheduler
            task = self.scheduler.get_next_task()
            
            if task:
                logger.info(f"▶️ Executing: {task['task_name']}")
                try:
                    # Jalankan fungsi task
                    task['func']() 
                    self.scheduler.complete_task(task['id'])
                except Exception as e:
                    logger.error(f"❌ Task failed: {e}")
                    await asyncio.sleep(10)
            
            # Heartbeat
            await asyncio.sleep(5)

    async def start(self):
        logger.info("🚀 Starting Instagram Bot...")
        self.setup_signal_handlers()
        self.running = True
        self.start_time = datetime.now()
        
        if not self.login_account():
            logger.error("❌ Failed to login. Exiting.")
            return

        # FIX 3: Telegram dimatikan sementara agar bot jalan dulu
        # await asyncio.gather(self.run_auto_actions(), self.run_telegram_bot())
        await self.run_auto_actions()

def main():
    print("""
    ╔══════════════════════════════════════╗
    ║      Instagram Bot v2.0              ║
    ║      Multi-Account Automation        ║
    ╚══════════════════════════════════════╝
    """)
    controller = BotController()
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(controller.start())
    except KeyboardInterrupt:
        controller.shutdown()
    except Exception as e:
        logger.critical(f"🔥 Critical Error: {e}")

if __name__ == "__main__":
    main()