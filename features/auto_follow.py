"""
Auto Follow Module
Otomatis follow user berdasarkan kriteria tertentu
"""

import time
import random
import json
from datetime import datetime
from pathlib import Path

class AutoFollow:
    def __init__(self, client, analytics=None, scheduler=None):
        self.client = client
        self.analytics = analytics
        self.scheduler = scheduler
        self.config = self._load_config()
        self.followed_users = self._load_followed_users()
        self.whitelist = self._load_whitelist()
        self.blacklist = self._load_blacklist()
        
    def _load_config(self):
        """Load konfigurasi auto follow"""
        return {
            "daily_limit": 50,
            "delay_min": 60,
            "delay_max": 180,
            "follow_probability": 0.6,
            "min_followers": 100,
            "max_followers": 50000,
            "min_following": 50,
            "max_following": 2000,
            "min_posts": 5,
            "skip_private": False,
            "skip_business": False,
            "skip_verified": True,
            "follow_back_only": False
        }
    
    def _load_followed_users(self):
        """Load daftar user yang sudah di-follow"""
        file_path = Path("data/followed_users.json")
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        return {}
    
    def _save_followed_users(self):
        """Simpan daftar user yang sudah di-follow"""
        Path("data").mkdir(exist_ok=True)
        with open("data/followed_users.json", "w") as f:
            json.dump(self.followed_users, f, indent=2)
    
    def _load_whitelist(self):
        """Load whitelist (jangan unfollow)"""
        file_path = Path("data/whitelist.json")
        if file_path.exists():
            with open(file_path, "r") as f:
                return set(json.load(f))
        return set()
    
    def _load_blacklist(self):
        """Load blacklist (jangan follow)"""
        file_path = Path("data/blacklist.json")
        if file_path.exists():
            with open(file_path, "r") as f:
                return set(json.load(f))
        return set()
    
    def _should_follow(self, user_info):
        """Cek apakah user layak di-follow"""
        try:
            username = user_info.username
            
            # Cek blacklist
            if username in self.blacklist:
                return False, "User dalam blacklist"
            
            # Cek sudah di-follow
            if username in self.followed_users:
                return False, "Sudah pernah di-follow"
            
            # Cek private
            if self.config["skip_private"] and user_info.is_private:
                return False, "Akun private"
            
            # Cek business
            if self.config["skip_business"] and user_info.is_business:
                return False, "Akun bisnis"
            
            # Cek verified
            if self.config["skip_verified"] and user_info.is_verified:
                return False, "Akun verified"
            
            # Cek followers
            followers = user_info.follower_count or 0
            if followers < self.config["min_followers"]:
                return False, f"Followers terlalu sedikit ({followers})"
            if followers > self.config["max_followers"]:
                return False, f"Followers terlalu banyak ({followers})"
            
            # Cek following
            following = user_info.following_count or 0
            if following < self.config["min_following"]:
                return False, f"Following terlalu sedikit ({following})"
            if following > self.config["max_following"]:
                return False, f"Following terlalu banyak ({following})"
            
            # Cek posts
            posts = user_info.media_count or 0
            if posts < self.config["min_posts"]:
                return False, f"Posts terlalu sedikit ({posts})"
            
            # Random probability
            if random.random() > self.config["follow_probability"]:
                return False, "Skip berdasarkan probability"
            
            return True, "OK"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def follow_user(self, username):
        """Follow single user"""
        try:
            username = username.lstrip("@")
            
            user_id = self.client.user_id_from_username(username)
            user_info = self.client.user_info(user_id)
            
            should_follow, reason = self._should_follow(user_info)
            if not should_follow:
                return {"success": False, "reason": reason}
            
            self.client.user_follow(user_id)
            
            # Simpan ke followed users
            self.followed_users[username] = {
                "user_id": str(user_id),
                "followed_at": datetime.now().isoformat(),
                "followers": user_info.follower_count,
                "following": user_info.following_count
            }
            self._save_followed_users()
            
            if self.analytics:
                self.analytics.track_action("follow", True, {"target": username})
            
            return {"success": True, "username": username}
            
        except Exception as e:
            if self.analytics:
                self.analytics.track_action("follow", False, {"error": str(e)})
            return {"success": False, "error": str(e)}
    
    def follow_followers_of(self, username, amount=10):
        """Follow followers dari user tertentu"""
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}
        
        try:
            username = username.lstrip("@")
            
            print(f"🔍 Mengambil followers dari @{username}...")
            user_id = self.client.user_id_from_username(username)
            followers = self.client.user_followers(user_id, amount=amount * 2)
            
            count = 0
            for user_id, user_info in followers.items():
                if count >= amount:
                    break
                
                try:
                    full_info = self.client.user_info(user_id)
                    should_follow, reason = self._should_follow(full_info)
                    
                    if not should_follow:
                        results["skipped"] += 1
                        print(f"⏭️ Skip @{user_info.username}: {reason}")
                        continue
                    
                    self.client.user_follow(user_id)
                    
                    self.followed_users[user_info.username] = {
                        "user_id": str(user_id),
                        "followed_at": datetime.now().isoformat(),
                        "source": f"followers_of_{username}"
                    }
                    
                    results["success"] += 1
                    count += 1
                    
                    if self.analytics:
                        self.analytics.track_action("follow", True, {
                            "source": "followers_of",
                            "source_user": username
                        })
                    
                    print(f"✅ Followed: @{user_info.username}")
                    
                    delay = random.randint(self.config["delay_min"], self.config["delay_max"])
                    print(f"⏳ Delay {delay} detik...")
                    time.sleep(delay)
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
                    print(f"❌ Error: {str(e)}")
            
            self._save_followed_users()
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def follow_by_hashtag(self, hashtag, amount=10):
        """Follow user yang post dengan hashtag tertentu"""
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}
        
        try:
            hashtag = hashtag.lstrip("#")
            
            print(f"🔍 Mencari user dengan hashtag #{hashtag}...")
            medias = self.client.hashtag_medias_recent(hashtag, amount=amount * 3)
            
            followed_usernames = set()
            count = 0
            
            for media in medias:
                if count >= amount:
                    break
                
                username = media.user.username
                
                if username in followed_usernames:
                    continue
                
                try:
                    user_info = self.client.user_info(media.user.pk)
                    should_follow, reason = self._should_follow(user_info)
                    
                    if not should_follow:
                        results["skipped"] += 1
                        continue
                    
                    self.client.user_follow(media.user.pk)
                    followed_usernames.add(username)
                    
                    self.followed_users[username] = {
                        "user_id": str(media.user.pk),
                        "followed_at": datetime.now().isoformat(),
                        "source": f"hashtag_{hashtag}"
                    }
                    
                    results["success"] += 1
                    count += 1
                    
                    if self.analytics:
                        self.analytics.track_action("follow", True, {
                            "source": "hashtag",
                            "hashtag": hashtag
                        })
                    
                    print(f"✅ Followed: @{username}")
                    
                    delay = random.randint(self.config["delay_min"], self.config["delay_max"])
                    time.sleep(delay)
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
            
            self._save_followed_users()
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def unfollow_non_followers(self, amount=10, days_old=3):
        """Unfollow user yang tidak follow back setelah X hari"""
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": []}
        
        try:
            print("🔍 Mengecek following yang tidak follow back...")
            
            # Dapatkan followers saat ini
            my_id = self.client.user_id
            my_followers = set(self.client.user_followers(my_id).keys())
            my_following = self.client.user_following(my_id)
            
            count = 0
            for user_id, user_info in my_following.items():
                if count >= amount:
                    break
                
                username = user_info.username
                
                # Skip whitelist
                if username in self.whitelist:
                    results["skipped"] += 1
                    continue
                
                # Cek apakah follow back
                if user_id in my_followers:
                    continue
                
                # Cek umur follow
                if username in self.followed_users:
                    followed_at = datetime.fromisoformat(
                        self.followed_users[username].get("followed_at", datetime.now().isoformat())
                    )
                    days_since = (datetime.now() - followed_at).days
                    
                    if days_since < days_old:
                        results["skipped"] += 1
                        continue
                
                try:
                    self.client.user_unfollow(user_id)
                    results["success"] += 1
                    count += 1
                    
                    # Hapus dari followed_users
                    if username in self.followed_users:
                        del self.followed_users[username]
                    
                    if self.analytics:
                        self.analytics.track_action("unfollow", True, {"target": username})
                    
                    print(f"👋 Unfollowed: @{username}")
                    
                    delay = random.randint(30, 90)
                    time.sleep(delay)
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
            
            self._save_followed_users()
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def get_stats(self):
        """Dapatkan statistik auto follow"""
        return {
            "total_followed": len(self.followed_users),
            "whitelist_count": len(self.whitelist),
            "blacklist_count": len(self.blacklist),
            "config": self.config
        }
