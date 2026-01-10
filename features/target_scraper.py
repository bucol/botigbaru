"""
Target Scraper Module
Scrape dan kumpulkan target users dari berbagai sumber
"""

import json
import time
import random
from datetime import datetime
from pathlib import Path

class TargetScraper:
    def __init__(self, client, analytics=None):
        self.client = client
        self.analytics = analytics
        self.config = self._load_config()
        self.scraped_users = {}
        
    def _load_config(self):
        """Load konfigurasi scraper"""
        return {
            "delay_min": 2,
            "delay_max": 5,
            "batch_size": 50,
            "save_format": "json",  # json, csv, txt
            "include_stats": True,
            "filter_private": False,
            "filter_verified": False,
            "min_followers": 0,
            "max_followers": 1000000,
            "min_posts": 0
        }
    
    def _save_results(self, users, filename, source_info):
        """Simpan hasil scraping"""
        Path("data/scraped").mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"data/scraped/{filename}_{timestamp}.json"
        
        data = {
            "source": source_info,
            "scraped_at": datetime.now().isoformat(),
            "total_users": len(users),
            "users": users
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def _filter_user(self, user_info):
        """Filter user berdasarkan kriteria"""
        try:
            # Filter private
            if self.config["filter_private"] and user_info.is_private:
                return False
            
            # Filter verified
            if self.config["filter_verified"] and user_info.is_verified:
                return False
            
            # Filter followers
            followers = user_info.follower_count or 0
            if followers < self.config["min_followers"]:
                return False
            if followers > self.config["max_followers"]:
                return False
            
            # Filter posts
            posts = user_info.media_count or 0
            if posts < self.config["min_posts"]:
                return False
            
            return True
        except:
            return True
    
    def _format_user(self, user_info, include_full=False):
        """Format user data untuk disimpan"""
        basic = {
            "username": user_info.username,
            "user_id": str(user_info.pk),
            "full_name": user_info.full_name
        }
        
        if include_full and self.config["include_stats"]:
            basic.update({
                "followers": user_info.follower_count,
                "following": user_info.following_count,
                "posts": user_info.media_count,
                "is_private": user_info.is_private,
                "is_verified": user_info.is_verified,
                "is_business": user_info.is_business,
                "biography": user_info.biography,
                "external_url": user_info.external_url
            })
        
        return basic
    
    def scrape_followers(self, username, amount=100):
        """Scrape followers dari user"""
        username = username.lstrip("@")
        users = []
        
        try:
            print(f"🔍 Scraping followers dari @{username}...")
            
            user_id = self.client.user_id_from_username(username)
            followers = self.client.user_followers(user_id, amount=amount)
            
            count = 0
            for uid, user_short in followers.items():
                if count >= amount:
                    break
                
                try:
                    # Get full info jika perlu filter/stats
                    if self.config["include_stats"]:
                        user_info = self.client.user_info(uid)
                        if not self._filter_user(user_info):
                            continue
                        users.append(self._format_user(user_info, include_full=True))
                    else:
                        users.append({
                            "username": user_short.username,
                            "user_id": str(uid),
                            "full_name": user_short.full_name
                        })
                    
                    count += 1
                    
                    if count % 10 == 0:
                        print(f"📊 Progress: {count}/{amount}")
                        delay = random.uniform(
                            self.config["delay_min"],
                            self.config["delay_max"]
                        )
                        time.sleep(delay)
                        
                except Exception as e:
                    print(f"⚠️ Error getting user info: {e}")
                    continue
            
            # Simpan hasil
            filepath = self._save_results(
                users,
                f"followers_{username}",
                {"type": "followers", "target": username}
            )
            
            if self.analytics:
                self.analytics.track_action("scrape", True, {
                    "type": "followers",
                    "target": username,
                    "count": len(users)
                })
            
            print(f"✅ Scraped {len(users)} followers dari @{username}")
            
            return {
                "success": True,
                "total": len(users),
                "file": filepath,
                "users": users
            }
            
        except Exception as e:
            print(f"❌ Error scraping followers: {e}")
            return {"success": False, "error": str(e), "users": users}
    
    def scrape_following(self, username, amount=100):
        """Scrape following dari user"""
        username = username.lstrip("@")
        users = []
        
        try:
            print(f"🔍 Scraping following dari @{username}...")
            
            user_id = self.client.user_id_from_username(username)
            following = self.client.user_following(user_id, amount=amount)
            
            count = 0
            for uid, user_short in following.items():
                if count >= amount:
                    break
                
                try:
                    if self.config["include_stats"]:
                        user_info = self.client.user_info(uid)
                        if not self._filter_user(user_info):
                            continue
                        users.append(self._format_user(user_info, include_full=True))
                    else:
                        users.append({
                            "username": user_short.username,
                            "user_id": str(uid),
                            "full_name": user_short.full_name
                        })
                    
                    count += 1
                    
                    if count % 10 == 0:
                        print(f"📊 Progress: {count}/{amount}")
                        time.sleep(random.uniform(
                            self.config["delay_min"],
                            self.config["delay_max"]
                        ))
                        
                except Exception as e:
                    continue
            
            filepath = self._save_results(
                users,
                f"following_{username}",
                {"type": "following", "target": username}
            )
            
            print(f"✅ Scraped {len(users)} following dari @{username}")
            
            return {
                "success": True,
                "total": len(users),
                "file": filepath,
                "users": users
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "users": users}
    
    def scrape_hashtag_users(self, hashtag, amount=100):
        """Scrape users yang post dengan hashtag tertentu"""
        hashtag = hashtag.lstrip("#")
        users = []
        seen_usernames = set()
        
        try:
            print(f"🔍 Scraping users dari #{hashtag}...")
            
            medias = self.client.hashtag_medias_recent(hashtag, amount=amount * 2)
            
            count = 0
            for media in medias:
                if count >= amount:
                    break
                
                username = media.user.username
                
                if username in seen_usernames:
                    continue
                seen_usernames.add(username)
                
                try:
                    if self.config["include_stats"]:
                        user_info = self.client.user_info(media.user.pk)
                        if not self._filter_user(user_info):
                            continue
                        user_data = self._format_user(user_info, include_full=True)
                        user_data["found_via_post"] = media.code
                        users.append(user_data)
                    else:
                        users.append({
                            "username": username,
                            "user_id": str(media.user.pk),
                            "full_name": media.user.full_name,
                            "found_via_post": media.code
                        })
                    
                    count += 1
                    
                    if count % 10 == 0:
                        print(f"📊 Progress: {count}/{amount}")
                        time.sleep(random.uniform(
                            self.config["delay_min"],
                            self.config["delay_max"]
                        ))
                        
                except Exception as e:
                    continue
            
            filepath = self._save_results(
                users,
                f"hashtag_{hashtag}",
                {"type": "hashtag", "hashtag": hashtag}
            )
            
            print(f"✅ Scraped {len(users)} users dari #{hashtag}")
            
            return {
                "success": True,
                "total": len(users),
                "file": filepath,
                "users": users
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "users": users}
    
    def scrape_likers(self, media_code, amount=100):
        """Scrape users yang like post tertentu"""
        users = []
        
        try:
            print(f"🔍 Scraping likers dari post {media_code}...")
            
            # Handle URL atau code
            if "instagram.com" in media_code:
                media_code = media_code.split("/p/")[1].split("/")[0]
            
            media_pk = self.client.media_pk_from_code(media_code)
            likers = self.client.media_likers(media_pk)
            
            count = 0
            for user_short in likers[:amount]:
                try:
                    if self.config["include_stats"]:
                        user_info = self.client.user_info(user_short.pk)
                        if not self._filter_user(user_info):
                            continue
                        users.append(self._format_user(user_info, include_full=True))
                    else:
                        users.append({
                            "username": user_short.username,
                            "user_id": str(user_short.pk),
                            "full_name": user_short.full_name
                        })
                    
                    count += 1
                    
                    if count % 20 == 0:
                        print(f"📊 Progress: {count}/{min(amount, len(likers))}")
                        time.sleep(random.uniform(
                            self.config["delay_min"],
                            self.config["delay_max"]
                        ))
                        
                except Exception as e:
                    continue
            
            filepath = self._save_results(
                users,
                f"likers_{media_code}",
                {"type": "likers", "media_code": media_code}
            )
            
            print(f"✅ Scraped {len(users)} likers")
            
            return {
                "success": True,
                "total": len(users),
                "file": filepath,
                "users": users
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "users": users}
    
    def scrape_commenters(self, media_code, amount=100):
        """Scrape users yang comment di post tertentu"""
        users = []
        seen_usernames = set()
        
        try:
            print(f"🔍 Scraping commenters dari post {media_code}...")
            
            if "instagram.com" in media_code:
                media_code = media_code.split("/p/")[1].split("/")[0]
            
            media_pk = self.client.media_pk_from_code(media_code)
            comments = self.client.media_comments(media_pk, amount=amount * 2)
            
            count = 0
            for comment in comments:
                if count >= amount:
                    break
                
                username = comment.user.username
                
                if username in seen_usernames:
                    continue
                seen_usernames.add(username)
                
                try:
                    if self.config["include_stats"]:
                        user_info = self.client.user_info(comment.user.pk)
                        if not self._filter_user(user_info):
                            continue
                        user_data = self._format_user(user_info, include_full=True)
                        user_data["comment"] = comment.text
                        users.append(user_data)
                    else:
                        users.append({
                            "username": username,
                            "user_id": str(comment.user.pk),
                            "full_name": comment.user.full_name,
                            "comment": comment.text
                        })
                    
                    count += 1
                    
                    if count % 20 == 0:
                        print(f"📊 Progress: {count}/{amount}")
                        time.sleep(random.uniform(
                            self.config["delay_min"],
                            self.config["delay_max"]
                        ))
                        
                except Exception as e:
                    continue
            
            filepath = self._save_results(
                users,
                f"commenters_{media_code}",
                {"type": "commenters", "media_code": media_code}
            )
            
            print(f"✅ Scraped {len(users)} commenters")
            
            return {
                "success": True,
                "total": len(users),
                "file": filepath,
                "users": users
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "users": users}
    
    def scrape_explore(self, amount=50):
        """Scrape users dari explore page"""
        users = []
        seen_usernames = set()
        
        try:
            print("🔍 Scraping users dari Explore...")
            
            medias = self.client.explore_medias(amount=amount * 2)
            
            count = 0
            for media in medias:
                if count >= amount:
                    break
                
                username = media.user.username
                
                if username in seen_usernames:
                    continue
                seen_usernames.add(username)
                
                try:
                    if self.config["include_stats"]:
                        user_info = self.client.user_info(media.user.pk)
                        if not self._filter_user(user_info):
                            continue
                        users.append(self._format_user(user_info, include_full=True))
                    else:
                        users.append({
                            "username": username,
                            "user_id": str(media.user.pk),
                            "full_name": media.user.full_name
                        })
                    
                    count += 1
                    
                except Exception as e:
                    continue
            
            filepath = self._save_results(
                users,
                "explore",
                {"type": "explore"}
            )
            
            print(f"✅ Scraped {len(users)} users dari Explore")
            
            return {
                "success": True,
                "total": len(users),
                "file": filepath,
                "users": users
            }
            
        except Exception as e:
            return {"success": False, "error": str(e), "users": users}
    
    def load_targets(self, filepath):
        """Load target users dari file hasil scraping"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            users = data.get("users", [])
            return {
                "success": True,
                "total": len(users),
                "users": users,
                "source": data.get("source", {})
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_stats(self):
        """Dapatkan statistik scraper"""
        scraped_dir = Path("data/scraped")
        files = list(scraped_dir.glob("*.json")) if scraped_dir.exists() else []
        
        return {
            "total_files": len(files),
            "config": self.config
        }
