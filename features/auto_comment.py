"""
Auto Comment Module - Enhanced "Humanized" Version
Fitur: SPINTAX Engine, Context Awareness, Emoji Randomizer
"""

import time
import random
import json
import logging
import re
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class AutoComment:
    def __init__(self, client, analytics=None, scheduler=None):
        self.client = client
        self.analytics = analytics
        self.config = self._load_config()
        self.commented_posts = self._load_json("data/commented_posts.json")
        
        # SPINTAX TEMPLATES (Sangat penting agar tidak terdeteksi spam)
        # Format: {Kata1|Kata2} {Kata3|Kata4}
        self.templates = {
            "general": [
                "{Wah|Wih|Wow} {keren|cakep|mantap} {banget|abiss|sih ini}! {🔥|🙌|👏}",
                "{Suka|Love} {banget|bgt} sama {kontennya|fotonya|ini}. {😍|✨}",
                "{Inspiratif|Bagus} {sekali|banget} kak! {Keep it up|Semangat} {🔥|💪}",
                "{Gokil|Keren} {fotonya|postingan ini}. {👍|👌}"
            ],
            "photo": [
                "{Tone|Warna|Vibe} fotonya {cakep|bagus} {banget|bgt} kak! {📸|✨}",
                "{Nice|Cool|Awesome} shot! {Suka|Love} {style-nya|angle-nya}. {🔥|👏}"
            ],
            "fashion": [
                "{Outfit|Style}-nya {kece|keren} {parah|banget}! {😍|🔥}",
                "{Suka|Naksir} sama {bajunya|gayanya} kak! {✨|💕}"
            ]
        }

    def _load_config(self):
        return {
            "daily_limit": random.randint(20, 40), # Comment limit harus rendah
            "comment_probability": 0.4, # Peluang komen kecil agar tidak spammy
            "skip_if_commented": True,
            "min_likes": 20,
            "max_likes": 5000
        }

    def _load_json(self, path):
        try:
            if Path(path).exists():
                with open(path, "r") as f:
                    return json.load(f)
        except Exception: pass
        return {}

    def _save_commented(self):
        with open("data/commented_posts.json", "w") as f:
            json.dump(self.commented_posts, f, indent=2)

    def _spin_text(self, text):
        """
        SPINTAX Engine: Mengubah '{A|B}' menjadi 'A' atau 'B' secara acak.
        Contoh: "{Hi|Hello} World" -> "Hi World" atau "Hello World"
        """
        pattern = r'\{([^{}]+)\}'
        while True:
            match = re.search(pattern, text)
            if not match:
                break
            options = match.group(1).split('|')
            chosen = random.choice(options)
            text = text[:match.start()] + chosen + text[match.end():]
        return text

    def _detect_category(self, media):
        caption = (media.caption_text or "").lower()
        if any(x in caption for x in ["ootd", "outfit", "style", "fashion"]):
            return "fashion"
        if media.media_type == 1:
            return "photo"
        return "general"

    def comment_by_hashtag(self, hashtag, limit=5):
        hashtag = hashtag.lstrip("#")
        results = {"success": 0, "skipped": 0}
        
        logger.info(f"💬 Looking for posts in #{hashtag} to comment...")
        try:
            medias = self.client.hashtag_medias_recent(hashtag, amount=limit * 2)
            random.shuffle(medias)

            count = 0
            for media in medias:
                if count >= limit: break
                
                # Filter
                if str(media.pk) in self.commented_posts:
                    continue
                if random.random() > self.config["comment_probability"]:
                    continue

                try:
                    category = self._detect_category(media)
                    raw_template = random.choice(self.templates.get(category, self.templates["general"]))
                    
                    # GENERATE UNIQUE COMMENT
                    final_comment = self._spin_text(raw_template)
                    
                    self.client.media_comment(media.pk, final_comment)
                    logger.info(f"🖊️ Commented on {media.code}: {final_comment}")
                    
                    self.commented_posts[str(media.pk)] = {
                        "text": final_comment,
                        "time": datetime.now().isoformat()
                    }
                    self._save_commented()
                    
                    if self.analytics:
                        self.analytics.track_action("comment", True, {"text": final_comment})
                        
                    count += 1
                    # Jeda komentar harus lama (Human: ngetik itu butuh waktu)
                    time.sleep(random.uniform(40, 120))
                    
                except Exception as e:
                    logger.error(f"❌ Comment failed: {e}")
                    time.sleep(60) # Penalty sleep jika error

        except Exception as e:
            logger.error(f"❌ Error fetching hashtag: {e}")
            
        return results