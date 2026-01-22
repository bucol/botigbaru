"""
Auto Follow Module - Enhanced "Humanized" Version
Fitur: Smart Filtering, Profile Visit Simulation, Safe Unfollow
"""

import time
import random
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AutoFollow:
    def __init__(self, client, analytics=None, scheduler=None):
        self.client = client
        self.analytics = analytics
        self.config = self._load_config()
        self.followed_users = self._load_json("data/followed_users.json")
        self.whitelist = set(self._load_json("data/whitelist.json", default=[]))
        self.blacklist = set(self._load_json("data/blacklist.json", default=[]))

    def _load_config(self):
        return {
            "daily_follow_limit": random.randint(40, 80), # Limit aman 2024
            "follow_prob": 0.7, # Tidak semua target di-follow
            "min_followers": 150,
            "max_followers": 10000,
            "min_posts": 3,
            "skip_private": True,
            "skip_business": True,
            "unfollow_after_days": 4
        }

    def _load_json(self, path, default=None):
        if default is None: default = {}
        try:
            if Path(path).exists():
                with open(path, "r") as f:
                    return json.load(f)
        except Exception:
            pass
        return default

    def _save_followed(self):
        with open("data/followed_users.json", "w") as f:
            json.dump(self.followed_users, f, indent=2)

    def _human_delay(self):
        """Delay lebih lama untuk aksi follow (High Risk Action)"""
        time.sleep(random.uniform(20, 60))

    def _should_follow(self, user_info):
        if user_info.username in self.blacklist or user_info.username in self.followed_users:
            return False, "Blacklisted/Already followed"
        
        if self.config["skip_private"] and user_info.is_private:
            return False, "Private account"
            
        if self.config["skip_business"] and user_info.is_business:
            return False, "Business account"
            
        if not (self.config["min_followers"] <= user_info.follower_count <= self.config["max_followers"]):
            return False, "Followers count criteria unmet"
            
        return True, "OK"

    def follow_user_followers(self, target_user, limit=10):
        """Follow followers dari akun target"""
        results = {"success": 0, "skipped": 0}
        try:
            target_id = self.client.user_id_from_username(target_user)
            logger.info(f"🔍 Scavenging followers from @{target_user}...")
            
            # Ambil followers random, jangan urut dari atas (pola bot)
            followers = self.client.user_followers(target_id, amount=limit * 3)
            candidate_ids = list(followers.keys())
            random.shuffle(candidate_ids)
            
            count = 0
            for uid in candidate_ids:
                if count >= limit: break
                
                try:
                    # 1. Simulasi "Visit Profile" (Ambil info user)
                    user_info = self.client.user_info(uid)
                    
                    # 2. Filter
                    should, reason = self._should_follow(user_info)
                    if not should:
                        logger.info(f"⏭️ Skip @{user_info.username}: {reason}")
                        results["skipped"] += 1
                        time.sleep(random.uniform(2, 5)) # Jeda pendek saat skip
                        continue
                        
                    # 3. Random Probability check
                    if random.random() > self.config["follow_prob"]:
                        logger.info(f"🎲 Skipped @{user_info.username} (Human Randomness)")
                        continue

                    # 4. Action Follow
                    self.client.user_follow(uid)
                    logger.info(f"➕ Followed @{user_info.username}")
                    
                    self.followed_users[user_info.username] = {
                        "id": str(uid),
                        "time": datetime.now().isoformat(),
                        "source": target_user
                    }
                    self._save_followed()
                    
                    if self.analytics:
                        self.analytics.track_action("follow", True, {"target": user_info.username})
                        
                    count += 1
                    self._human_delay()
                    
                except Exception as e:
                    logger.error(f"❌ Failed to follow {uid}: {e}")
                    time.sleep(30)

        except Exception as e:
            logger.error(f"❌ Error getting followers: {e}")
            
        return results

    def smart_unfollow(self, limit=10):
        """Unfollow user yang sudah lama (FIFO) dan tidak ada di whitelist"""
        logger.info("🔪 Starting Smart Unfollow...")
        count = 0
        
        # Sort based on followed time (Oldest first)
        candidates = []
        for uname, data in self.followed_users.items():
            if uname in self.whitelist: continue
            
            followed_time = datetime.fromisoformat(data["time"])
            if datetime.now() - followed_time > timedelta(days=self.config["unfollow_after_days"]):
                candidates.append((uname, data["id"]))
                
        # Shuffle sedikit agar tidak persis urutan waktu
        random.shuffle(candidates)
        
        for uname, uid in candidates[:limit]:
            try:
                # Cek apakah dia followback? (Opsional, memakan request)
                # friendship = self.client.user_friendship(uid)
                # if friendship.following: continue # Jika dia followback, jangan unfollow
                
                self.client.user_unfollow(uid)
                logger.info(f"➖ Unfollowed @{uname}")
                
                del self.followed_users[uname]
                self._save_followed()
                count += 1
                
                self._human_delay()
                
            except Exception as e:
                logger.error(f"❌ Unfollow error: {e}")
                
        return {"unfollowed": count}