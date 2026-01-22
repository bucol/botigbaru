"""
Auto Story Viewer - Humanized Version
Fitur: Smart Skipping, Variable Duration, Safe Reactions
"""

import time
import json
import random
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AutoStory:
    def __init__(self, client):
        self.client = client
        self.data_file = Path("data/viewed_stories.json")
        self.viewed_stories = self._load_viewed()
        
        # Config Humanis
        self.config = {
            'daily_limit': random.randint(150, 300),
            'view_duration_photo': (1.5, 4.0), # Foto dilihat sekilas
            'view_duration_video': (5.0, 15.0), # Video dilihat agak lama
            'skip_probability': 0.3, # 30% peluang skip story teman (tap next)
            'react_probability': 0.05, # JANGAN sering-sering react! Bahaya.
            'reply_probability': 0.02  # Reply sangat jarang
        }
        
        self.reactions = ['😍', '🔥', '👏', '❤️', '😂']
        # Spintax templates untuk reply
        self.reply_templates = [
            "{Keren|Mantap|Gokil} {banget|abiss} {🔥|👏}",
            "{Wow|Wih} {keren|cakep}! {😍|✨}",
            "{Suka|Love} {banget|bgt} {❤️|💕}",
            "{Setuju|Valid} {banget|bgt} {sih|ini} {💯|👍}"
        ]
        
        self.stats = {'viewed': 0, 'reacted': 0, 'replied': 0}

    def _load_viewed(self):
        try:
            if self.data_file.exists():
                data = json.loads(self.data_file.read_text())
                # Reset jika hari berganti
                if data.get('date') != str(datetime.now().date()):
                    return {'stories': [], 'date': str(datetime.now().date())}
                return data
        except Exception:
            pass
        return {'stories': [], 'date': str(datetime.now().date())}

    def _save_viewed(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self.viewed_stories, indent=2))

    def _spin_text(self, text):
        import re
        pattern = r'\{([^{}]+)\}'
        while True:
            match = re.search(pattern, text)
            if not match: break
            options = match.group(1).split('|')
            text = text[:match.start()] + random.choice(options) + text[match.end():]
        return text

    def view_user_stories(self, username):
        """View stories user tertentu dengan pola manusia (bisa skip)"""
        result = {'viewed': 0, 'reacted': 0}
        
        try:
            user_id = self.client.user_id_from_username(username)
            stories = self.client.user_stories(user_id)
            
            if not stories:
                return result

            # Manusia biasanya lihat story urut, tapi bisa skip di tengah jalan
            for story in stories:
                story_id = str(story.pk)
                
                # Cek limit harian
                if self.stats['viewed'] >= self.config['daily_limit']:
                    logger.warning("⚠️ Daily story limit reached.")
                    break

                # Skip jika sudah dilihat
                if story_id in self.viewed_stories['stories']:
                    continue

                # SIMULASI SKIP (Tap Next)
                # Jika user punya banyak story, kita kadang skip beberapa
                if random.random() < self.config['skip_probability']:
                    # Kita tandai 'viewed' tapi durasinya super cepat (0.1s - 0.5s) seolah tap cepat
                    time.sleep(random.uniform(0.1, 0.5))
                    self.client.story_seen([story.pk]) 
                    self.viewed_stories['stories'].append(story_id)
                    continue

                # View normal
                try:
                    self.client.story_seen([story.pk])
                    
                    # Durasi nonton tergantung tipe konten
                    if story.video_duration: # Kalau video
                        dur = random.uniform(*self.config['view_duration_video'])
                    else: # Kalau foto
                        dur = random.uniform(*self.config['view_duration_photo'])
                    
                    time.sleep(dur)
                    
                    self.viewed_stories['stories'].append(story_id)
                    self.stats['viewed'] += 1
                    result['viewed'] += 1

                    # Interaksi (React/Reply) - Hanya jika benar-benar nonton (tidak skip)
                    self._handle_interaction(story, user_id)
                    
                except Exception as e:
                    logger.error(f"❌ Failed view story {story_id}: {e}")

            self._save_viewed()
            
        except Exception as e:
            logger.error(f"❌ Error viewing {username}: {e}")
            
        return result

    def _handle_interaction(self, story, user_id):
        """Logic reaksi yang aman"""
        # Jangan react ke semua story, pilih satu per user per sesi
        if random.random() < self.config['react_probability']:
            try:
                reaction = random.choice(self.reactions)
                self.client.story_send_reaction(story.pk, reaction)
                logger.info(f"❤️ Sent reaction {reaction} to story")
                self.stats['reacted'] += 1
                time.sleep(random.uniform(2, 5))
                return # Sudah react, jangan reply lagi
            except: pass

        if random.random() < self.config['reply_probability']:
            try:
                raw_tpl = random.choice(self.reply_templates)
                msg = self._spin_text(raw_tpl)
                self.client.direct_send(msg, user_ids=[user_id])
                logger.info(f"💬 Replied to story: {msg}")
                self.stats['replied'] += 1
                time.sleep(random.uniform(5, 10))
            except: pass

    def view_following_stories(self, limit=20):
        """Nonton story dari feed (seperti manusia scroll beranda)"""
        logger.info("👀 Watching stories from feed...")
        try:
            # Ambil reel tray (lingkaran story di atas beranda)
            reels_tray = self.client.reels_tray()
            # Shuffle biar gak selalu urutan awal
            random.shuffle(reels_tray)
            
            processed = 0
            for reel in reels_tray:
                if processed >= limit: break
                
                username = reel.user.username
                logger.info(f"▶️ Viewing @{username}'s stories")
                
                res = self.view_user_stories(username)
                if res['viewed'] > 0:
                    processed += 1
                    # Jeda antar user (seperti pindah profile)
                    time.sleep(random.uniform(3, 8))
                    
        except Exception as e:
            logger.error(f"❌ Error viewing feed: {e}")
            
        return self.stats