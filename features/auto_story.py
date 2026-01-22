"""
Auto Story Viewer - Humanized Version (Fixed API)
"""

import time
import json
import random
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class AutoStory:
    def __init__(self, client):
        self.client = client
        self.data_file = Path("data/viewed_stories.json")
        self.viewed_stories = self._load_viewed()
        
        self.config = {
            'daily_limit': random.randint(150, 300),
            'view_duration_photo': (1.5, 4.0),
            'view_duration_video': (5.0, 15.0),
            'skip_probability': 0.3,
            'react_probability': 0.05,
            'reply_probability': 0.02
        }
        
        self.reactions = ['😍', '🔥', '👏', '❤️', '😂']
        self.reply_templates = [
            "{Keren|Mantap|Gokil} {banget|abiss} {🔥|👏}",
            "{Wow|Wih} {keren|cakep}! {😍|✨}",
            "{Suka|Love} {banget|bgt} {❤️|💕}"
        ]
        
        self.stats = {'viewed': 0, 'reacted': 0, 'replied': 0}

    def _load_viewed(self):
        try:
            if self.data_file.exists():
                data = json.loads(self.data_file.read_text())
                if data.get('date') != str(datetime.now().date()):
                    return {'stories': [], 'date': str(datetime.now().date())}
                return data
        except Exception: pass
        return {'stories': [], 'date': str(datetime.now().date())}

    def _save_viewed(self):
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self.viewed_stories, indent=2))

    def view_following_stories(self, limit=20):
        """Nonton story dari feed (FIXED METHOD)"""
        logger.info("👀 Watching stories from feed...")
        try:
            # FIX: Gunakan get_reels_tray() bukan reels_tray()
            reels_tray = self.client.get_reels_tray()
            random.shuffle(reels_tray)
            
            processed = 0
            for reel in reels_tray:
                if processed >= limit: break
                
                # Skip jika user ini sudah dilihat semua storynya
                if reel.seen:
                    continue

                username = reel.user.username
                logger.info(f"▶️ Viewing @{username}'s stories")
                
                # Logic view manual per item di dalam reel
                count_viewed = 0
                for item in reel.items:
                    story_id = str(item.pk)
                    if story_id in self.viewed_stories['stories']:
                        continue
                        
                    self.client.story_seen([item.pk])
                    self.viewed_stories['stories'].append(story_id)
                    count_viewed += 1
                    time.sleep(random.uniform(1, 3)) # Jeda antar slide
                
                if count_viewed > 0:
                    self.stats['viewed'] += count_viewed
                    processed += 1
                    self._save_viewed()
                    time.sleep(random.uniform(3, 8)) # Jeda antar user
            
            logger.info(f"✅ Auto Story finished. Total viewed: {self.stats['viewed']}")
                    
        except Exception as e:
            logger.error(f"❌ Error viewing feed: {e}")
            
        return self.stats