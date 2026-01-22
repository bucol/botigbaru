"""
Auto Like Module - Enhanced "Humanized" Version
Fitur: Smart Sleep, View Simulation, & Random Skipping
"""

import time
import random
import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class AutoLike:
    def __init__(self, client, analytics=None, scheduler=None):
        self.client = client
        self.analytics = analytics
        self.scheduler = scheduler
        self.config = self._load_config()
        self.liked_posts = self._load_liked_posts()
        
        # Buat folder data jika belum ada
        Path("data").mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        return {
            "daily_limit": random.randint(80, 150), # Limit harian acak setiap bot start
            "like_probability": 0.85, 
            "skip_if_liked": True,
            "skip_video": False,
            "min_likes": 5,
            "max_likes": 50000,
            "action_delay_range": (5, 25), # Waktu antar like (cepat)
            "batch_break_range": (120, 600) # Istirahat panjang setiap beberapa like
        }

    def _load_liked_posts(self):
        try:
            path = Path("data/liked_posts.json")
            if path.exists():
                with open(path, "r") as f:
                    return set(json.load(f))
        except Exception:
            pass
        return set()

    def _save_liked_posts(self):
        with open("data/liked_posts.json", "w") as f:
            json.dump(list(self.liked_posts), f)

    def _human_sleep(self):
        """Tidur dengan pola manusia (dominan cepat, kadang lambat)"""
        # 80% peluang tidur sebentar (scroll feed), 20% tidur lama (baca/nonton)
        if random.random() < 0.8:
            sleep_time = random.uniform(*self.config["action_delay_range"])
        else:
            sleep_time = random.uniform(30, 90)
        
        logger.info(f"⏳ Waiting {sleep_time:.1f}s...")
        time.sleep(sleep_time)

    def _should_like(self, media):
        """Filter cerdas"""
        media_id = str(media.pk)
        
        if self.config["skip_if_liked"] and media_id in self.liked_posts:
            return False, "Already liked"
            
        if self.config["skip_video"] and media.media_type == 2:
            return False, "Video skipped"
            
        # Analisa jumlah like (hindari akun terlalu sepi atau terlalu viral)
        if not (self.config["min_likes"] <= media.like_count <= self.config["max_likes"]):
            return False, f"Like count {media.like_count} out of range"

        # Simulasi "Mood" (Random skip)
        if random.random() > self.config["like_probability"]:
            return False, "Skipped by probability (Human mood)"

        return True, "OK"

    def process_media_list(self, medias, source_info):
        """Helper function untuk memproses list media"""
        results = {"success": 0, "failed": 0, "skipped": 0}
        
        for i, media in enumerate(medias):
            # Simulasi istirahat panjang setiap 5-10 like
            if i > 0 and i % random.randint(5, 10) == 0:
                long_break = random.randint(*self.config["batch_break_range"])
                logger.info(f"☕ Taking a coffee break for {long_break}s...")
                time.sleep(long_break)

            try:
                should, reason = self._should_like(media)
                if not should:
                    results["skipped"] += 1
                    logger.info(f"⏭️ Skip: {reason}")
                    continue

                # SIMULASI: Lihat media dulu sebelum like (Penting untuk anti-detect)
                # self.client.media_info(media.pk) # Opsional: uncomment jika ingin super aman (tapi boros request)
                
                self.client.media_like(media.pk)
                self.liked_posts.add(str(media.pk))
                results["success"] += 1
                
                logger.info(f"❤️ Liked {media.code} | Src: {source_info}")
                
                if self.analytics:
                    self.analytics.track_action("like", True, {"source": source_info, "media_id": media.pk})

                self._save_liked_posts()
                self._human_sleep()

            except Exception as e:
                logger.error(f"❌ Like failed: {e}")
                results["failed"] += 1
                time.sleep(10) # Safety sleep error

        return results

    def like_by_hashtag(self, hashtag, limit=10):
        hashtag = hashtag.lstrip("#")
        logger.info(f"🔍 Exploring hashtag #{hashtag}...")
        try:
            # Ambil lebih banyak media untuk filter
            medias = self.client.hashtag_medias_recent(hashtag, amount=limit * 2)
            # Acak urutan agar tidak selalu like postingan teratas (Top Recent)
            random.shuffle(medias)
            return self.process_media_list(medias[:limit], f"#{hashtag}")
        except Exception as e:
            logger.error(f"❌ Error fetching hashtag: {e}")
            return {}

    def like_by_user(self, username, limit=5):
        try:
            user_id = self.client.user_id_from_username(username)
            logger.info(f"🔍 Stalking @{username}...")
            medias = self.client.user_medias(user_id, amount=limit)
            return self.process_media_list(medias, f"user_@{username}")
        except Exception as e:
            logger.error(f"❌ Error fetching user media: {e}")
            return {}