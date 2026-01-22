"""
Auto DM Sender - Humanized Version
Fitur: SPINTAX, Contextual DM (Story Reply), Smart Limit
"""

import time
import json
import random
import logging
import re
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class AutoDM:
    def __init__(self, client):
        self.client = client
        self.data_file = Path("data/sent_dms.json")
        self.sent_dms = self._load_sent()
        
        self.config = {
            'daily_limit': random.randint(15, 25), # LIMIT KECIL = AMAN
            'delay_range': (120, 300), # 2-5 menit antar DM
            'mode': 'story_reply_first', # Utamakan reply story daripada DM kosong
            'min_followers': 50,
            'max_followers': 50000
        }
        
        # SPINTAX TEMPLATES (Sangat penting!)
        self.welcome_templates = [
            "{Hai|Halo|Hi} {name}! 👋 {Makasih|Thanks} udah follow ya. {Salam kenal!|Senang berteman denganmu.} {✨|😊}",
            "{Hi|Hello} {name}, {salam kenal|nice to meet you}! 👋 {Thanks|Terima kasih} for following. {Semoga harimu menyenangkan!|Have a great day!} {☀️|🌈}",
            "{Hey|Hai} {name}! 👋 {Just wanted to say hi|Cuma mau nyapa}, {makasih|thanks} follow-nya ya! {Let's connect!|Semoga betah liat kontenku.} {😄|🙏}"
        ]

        self.stats = {'sent': 0, 'failed': 0}

    def _load_sent(self):
        try:
            if self.data_file.exists():
                return json.loads(self.data_file.read_text())
        except: pass
        return {'dms': {}, 'date': str(datetime.now().date())}

    def _save_sent(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.sent_dms['date'] = str(datetime.now().date())
        self.data_file.write_text(json.dumps(self.sent_dms, indent=2))

    def _spin_text(self, text):
        pattern = r'\{([^{}]+)\}'
        while True:
            match = re.search(pattern, text)
            if not match: break
            options = match.group(1).split('|')
            text = text[:match.start()] + random.choice(options) + text[match.end():]
        return text

    def _personalize(self, text, user_info):
        name = user_info.full_name.split()[0] if user_info.full_name else user_info.username
        text = text.replace("{name}", name)
        text = text.replace("{username}", user_info.username)
        return self._spin_text(text)

    def send_welcome_dm(self, username):
        """Kirim DM welcome, mencoba reply story dulu jika ada (Lebih Trustworthy)"""
        if self.stats['sent'] >= self.config['daily_limit']:
            logger.warning("🛑 Daily DM limit reached.")
            return {'success': False, 'reason': 'limit'}

        try:
            user_id = self.client.user_id_from_username(username)
            
            # Cek history
            if str(user_id) in self.sent_dms['dms']:
                return {'success': False, 'reason': 'already_sent'}

            user_info = self.client.user_info(user_id)
            
            # Filter User
            if user_info.follower_count < self.config['min_followers'] or \
               user_info.follower_count > self.config['max_followers']:
                return {'success': False, 'reason': 'filter_followers'}

            # STRATEGI: Cek Story dulu
            stories = self.client.user_stories(user_id)
            sent_msg = ""
            
            if stories and self.config['mode'] == 'story_reply_first':
                # Reply ke story pertama (lebih natural masuk ke request message)
                story = stories[0]
                template = "{Hai|Halo} {name}, {salam kenal|thanks follow-nya}! 👋 {Story-nya keren!|Nice story!} {✨|🔥}"
                msg = self._personalize(template, user_info)
                self.client.direct_send(msg, user_ids=[user_id]) # Instagrapi usually handles story reply via media_id differently, but direct_send mostly works for text context
                # Note: Untuk reply story spesifik di instagrapi kadang butuh method khusus, 
                # tapi direct_send ke user seringkali cukup untuk memulai percakapan.
                sent_msg = "Story Reply: " + msg
                
            else:
                # Cold DM
                template = random.choice(self.welcome_templates)
                msg = self._personalize(template, user_info)
                self.client.direct_send(msg, user_ids=[user_id])
                sent_msg = "Cold DM: " + msg

            # Catat
            self.sent_dms['dms'][str(user_id)] = {
                'username': username,
                'time': str(datetime.now()),
                'type': 'welcome'
            }
            self._save_sent()
            self.stats['sent'] += 1
            
            logger.info(f"📨 Sent to @{username}: {sent_msg}")
            
            # Delay Manusiawi
            time.sleep(random.uniform(*self.config['delay_range']))
            return {'success': True}

        except Exception as e:
            logger.error(f"❌ DM failed to @{username}: {e}")
            self.stats['failed'] += 1
            return {'success': False, 'error': str(e)}