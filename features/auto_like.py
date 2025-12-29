"""
Auto Like Module
Otomatis like postingan berdasarkan target (hashtag/user/explore)
"""

import time
import random
import json
from datetime import datetime
from pathlib import Path

class AutoLike:
    def __init__(self, client, analytics=None, scheduler=None):
        self.client = client
        self.analytics = analytics
        self.scheduler = scheduler
        self.config = self._load_config()
        self.liked_posts = self._load_liked_posts()
        
    def _load_config(self):
        """Load konfigurasi auto like"""
        return {
            "daily_limit": 100,
            "delay_min": 30,
            "delay_max": 120,
            "like_probability": 0.7,  # 70% chance to like
            "skip_if_liked": True,
            "skip_video": False,
            "min_likes": 10,
            "max_likes": 10000,
            "min_followers": 100,
            "max_followers": 50000
        }
    
    def _load_liked_posts(self):
        """Load daftar post yang sudah di-like"""
        liked_file = Path("data/liked_posts.json")
        if liked_file.exists():
            with open(liked_file, "r") as f:
                return set(json.load(f))
        return set()
    
    def _save_liked_posts(self):
        """Simpan daftar post yang sudah di-like"""
        Path("data").mkdir(exist_ok=True)
        with open("data/liked_posts.json", "w") as f:
            json.dump(list(self.liked_posts), f)
    
    def _should_like(self, media):
        """Cek apakah post layak di-like"""
        try:
            # Skip jika sudah di-like
            if self.config["skip_if_liked"] and str(media.pk) in self.liked_posts:
                return False, "Sudah pernah di-like"
            
            # Skip video jika dikonfigurasi
            if self.config["skip_video"] and media.media_type == 2:
                return False, "Skip video"
            
            # Cek jumlah likes
            like_count = media.like_count or 0
            if like_count < self.config["min_likes"]:
                return False, f"Likes terlalu sedikit ({like_count})"
            if like_count > self.config["max_likes"]:
                return False, f"Likes terlalu banyak ({like_count})"
            
            # Random probability
            if random.random() > self.config["like_probability"]:
                return False, "Skip berdasarkan probability"
            
            return True, "OK"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def like_by_hashtag(self, hashtag, amount=10):
        """Like postingan berdasarkan hashtag"""
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}
        
        try:
            # Hapus # jika ada
            hashtag = hashtag.lstrip("#")
            
            print(f"🔍 Mencari postingan dengan hashtag #{hashtag}...")
            medias = self.client.hashtag_medias_recent(hashtag, amount=amount * 2)
            
            for media in medias[:amount]:
                try:
                    should_like, reason = self._should_like(media)
                    
                    if not should_like:
                        results["skipped"] += 1
                        print(f"⏭️ Skip: {reason}")
                        continue
                    
                    # Like post
                    self.client.media_like(media.pk)
                    self.liked_posts.add(str(media.pk))
                    results["success"] += 1
                    
                    # Track analytics
                    if self.analytics:
                        self.analytics.track_action("like", True, {
                            "source": "hashtag",
                            "hashtag": hashtag,
                            "media_id": str(media.pk)
                        })
                    
                    print(f"❤️ Liked: {media.code} (by @{media.user.username})")
                    
                    # Delay
                    delay = random.randint(
                        self.config["delay_min"], 
                        self.config["delay_max"]
                    )
                    print(f"⏳ Delay {delay} detik...")
                    time.sleep(delay)
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
                    print(f"❌ Error: {str(e)}")
                    
                    if self.analytics:
                        self.analytics.track_action("like", False, {"error": str(e)})
            
            # Save liked posts
            self._save_liked_posts()
            
        except Exception as e:
            results["errors"].append(f"Hashtag error: {str(e)}")
            print(f"❌ Error hashtag: {str(e)}")
        
        return results
    
    def like_by_user(self, username, amount=10):
        """Like postingan dari user tertentu"""
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}
        
        try:
            username = username.lstrip("@")
            
            print(f"🔍 Mencari postingan dari @{username}...")
            user_id = self.client.user_id_from_username(username)
            medias = self.client.user_medias(user_id, amount=amount)
            
            for media in medias:
                try:
                    should_like, reason = self._should_like(media)
                    
                    if not should_like:
                        results["skipped"] += 1
                        continue
                    
                    self.client.media_like(media.pk)
                    self.liked_posts.add(str(media.pk))
                    results["success"] += 1
                    
                    if self.analytics:
                        self.analytics.track_action("like", True, {
                            "source": "user",
                            "target_user": username
                        })
                    
                    print(f"❤️ Liked: {media.code}")
                    
                    delay = random.randint(self.config["delay_min"], self.config["delay_max"])
                    time.sleep(delay)
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
            
            self._save_liked_posts()
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def like_explore(self, amount=10):
        """Like postingan dari explore page"""
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}
        
        try:
            print("🔍 Mengambil postingan dari Explore...")
            medias = self.client.explore_medias(amount=amount * 2)
            
            for media in medias[:amount]:
                try:
                    should_like, reason = self._should_like(media)
                    
                    if not should_like:
                        results["skipped"] += 1
                        continue
                    
                    self.client.media_like(media.pk)
                    self.liked_posts.add(str(media.pk))
                    results["success"] += 1
                    
                    if self.analytics:
                        self.analytics.track_action("like", True, {"source": "explore"})
                    
                    print(f"❤️ Liked from explore: {media.code}")
                    
                    delay = random.randint(self.config["delay_min"], self.config["delay_max"])
                    time.sleep(delay)
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
            
            self._save_liked_posts()
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def get_stats(self):
        """Dapatkan statistik auto like"""
        return {
            "total_liked": len(self.liked_posts),
            "config": self.config
        }
