"""
Auto Comment Module
Otomatis comment pada postingan dengan template atau AI-generated
"""

import time
import random
import json
from datetime import datetime
from pathlib import Path

class AutoComment:
    def __init__(self, client, analytics=None, scheduler=None):
        self.client = client
        self.analytics = analytics
        self.scheduler = scheduler
        self.config = self._load_config()
        self.commented_posts = self._load_commented_posts()
        self.templates = self._load_templates()
        
    def _load_config(self):
        """Load konfigurasi auto comment"""
        return {
            "daily_limit": 30,
            "delay_min": 120,
            "delay_max": 300,
            "comment_probability": 0.5,
            "skip_if_commented": True,
            "min_likes": 50,
            "max_likes": 50000,
            "add_emoji": True,
            "vary_comments": True
        }
    
    def _load_commented_posts(self):
        """Load daftar post yang sudah di-comment"""
        file_path = Path("data/commented_posts.json")
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        return {}
    
    def _save_commented_posts(self):
        """Simpan daftar post yang sudah di-comment"""
        Path("data").mkdir(exist_ok=True)
        with open("data/commented_posts.json", "w") as f:
            json.dump(self.commented_posts, f, indent=2)
    
    def _load_templates(self):
        """Load template comment"""
        return {
            "general": [
                "Keren banget! 🔥",
                "Mantap! 👏",
                "Suka banget sama ini! ❤️",
                "Inspiratif! ✨",
                "Bagus banget! 😍",
                "Amazing! 🙌",
                "Love this! 💕",
                "So good! 👍",
                "Wow! 😮",
                "Aesthetic banget! 🌟"
            ],
            "photo": [
                "Fotonya keren! 📸",
                "Nice shot! 🎯",
                "Estetik banget! ✨",
                "Cakep! 😍",
                "Lighting-nya perfect! 💡"
            ],
            "food": [
                "Looks delicious! 😋",
                "Bikin laper! 🤤",
                "Yummy! 😍",
                "Mau dong! 🙋",
                "Mantap jiwa! 🔥"
            ],
            "travel": [
                "Pengen ke sana! ✈️",
                "View-nya amazing! 🏞️",
                "Bucket list! 📝",
                "Paradise! 🌴",
                "Kapan ke sini ya? 🤔"
            ],
            "fashion": [
                "Style-nya kece! 👗",
                "OOTD goals! 🎯",
                "Fashionable! 💅",
                "Slay! 🔥",
                "Outfit-nya cakep! 😍"
            ],
            "selfie": [
                "Glowing! ✨",
                "Cantik/Ganteng! 😍",
                "Senyumnya manis! 😊",
                "Photogenic banget! 📸",
                "Gemesin! 🥰"
            ]
        }
    
    def _get_comment(self, category="general", caption=""):
        """Generate comment berdasarkan kategori"""
        templates = self.templates.get(category, self.templates["general"])
        comment = random.choice(templates)
        
        if self.config["vary_comments"]:
            # Tambahkan variasi
            variations = ["", " 👌", " 💯", " nih", " ya", " dong"]
            comment += random.choice(variations)
        
        return comment
    
    def _detect_category(self, media):
        """Deteksi kategori post berdasarkan caption"""
        caption = (media.caption_text or "").lower()
        
        food_keywords = ["makan", "food", "kuliner", "yummy", "delicious", "restaurant", "cafe"]
        travel_keywords = ["travel", "vacation", "holiday", "trip", "explore", "beach", "mountain"]
        fashion_keywords = ["ootd", "outfit", "fashion", "style", "wear", "dress", "look"]
        selfie_keywords = ["selfie", "me", "aku", "gue", "gw"]
        
        if any(kw in caption for kw in food_keywords):
            return "food"
        elif any(kw in caption for kw in travel_keywords):
            return "travel"
        elif any(kw in caption for kw in fashion_keywords):
            return "fashion"
        elif any(kw in caption for kw in selfie_keywords):
            return "selfie"
        elif media.media_type == 1:  # Photo
            return "photo"
        else:
            return "general"
    
    def _should_comment(self, media):
        """Cek apakah post layak di-comment"""
        try:
            media_id = str(media.pk)
            
            if self.config["skip_if_commented"] and media_id in self.commented_posts:
                return False, "Sudah pernah di-comment"
            
            like_count = media.like_count or 0
            if like_count < self.config["min_likes"]:
                return False, f"Likes terlalu sedikit ({like_count})"
            if like_count > self.config["max_likes"]:
                return False, f"Likes terlalu banyak ({like_count})"
            
            if random.random() > self.config["comment_probability"]:
                return False, "Skip berdasarkan probability"
            
            return True, "OK"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def comment_post(self, media_id, comment_text=None):
        """Comment pada single post"""
        try:
            media = self.client.media_info(media_id)
            
            if not comment_text:
                category = self._detect_category(media)
                comment_text = self._get_comment(category, media.caption_text)
            
            self.client.media_comment(media_id, comment_text)
            
            self.commented_posts[str(media_id)] = {
                "commented_at": datetime.now().isoformat(),
                "comment": comment_text,
                "username": media.user.username
            }
            self._save_commented_posts()
            
            if self.analytics:
                self.analytics.track_action("comment", True, {
                    "media_id": str(media_id),
                    "comment": comment_text
                })
            
            return {"success": True, "comment": comment_text}
            
        except Exception as e:
            if self.analytics:
                self.analytics.track_action("comment", False, {"error": str(e)})
            return {"success": False, "error": str(e)}
    
    def comment_by_hashtag(self, hashtag, amount=5):
        """Comment pada postingan dengan hashtag tertentu"""
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": [], "comments": []}
        
        try:
            hashtag = hashtag.lstrip("#")
            
            print(f"🔍 Mencari postingan dengan hashtag #{hashtag}...")
            medias = self.client.hashtag_medias_recent(hashtag, amount=amount * 3)
            
            count = 0
            for media in medias:
                if count >= amount:
                    break
                
                try:
                    should_comment, reason = self._should_comment(media)
                    
                    if not should_comment:
                        results["skipped"] += 1
                        print(f"⏭️ Skip: {reason}")
                        continue
                    
                    category = self._detect_category(media)
                    comment_text = self._get_comment(category)
                    
                    self.client.media_comment(media.pk, comment_text)
                    
                    self.commented_posts[str(media.pk)] = {
                        "commented_at": datetime.now().isoformat(),
                        "comment": comment_text,
                        "hashtag": hashtag
                    }
                    
                    results["success"] += 1
                    results["comments"].append({
                        "post": media.code,
                        "comment": comment_text
                    })
                    count += 1
                    
                    if self.analytics:
                        self.analytics.track_action("comment", True, {
                            "source": "hashtag",
                            "hashtag": hashtag
                        })
                    
                    print(f"💬 Commented on {media.code}: '{comment_text}'")
                    
                    delay = random.randint(self.config["delay_min"], self.config["delay_max"])
                    print(f"⏳ Delay {delay} detik...")
                    time.sleep(delay)
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
                    print(f"❌ Error: {str(e)}")
            
            self._save_commented_posts()
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def comment_user_posts(self, username, amount=3):
        """Comment pada postingan user tertentu"""
        results = {"success": 0, "failed": 0, "skipped": 0, "errors": [], "comments": []}
        
        try:
            username = username.lstrip("@")
            
            print(f"🔍 Mencari postingan dari @{username}...")
            user_id = self.client.user_id_from_username(username)
            medias = self.client.user_medias(user_id, amount=amount * 2)
            
            count = 0
            for media in medias:
                if count >= amount:
                    break
                
                try:
                    should_comment, reason = self._should_comment(media)
                    
                    if not should_comment:
                        results["skipped"] += 1
                        continue
                    
                    category = self._detect_category(media)
                    comment_text = self._get_comment(category)
                    
                    self.client.media_comment(media.pk, comment_text)
                    
                    self.commented_posts[str(media.pk)] = {
                        "commented_at": datetime.now().isoformat(),
                        "comment": comment_text,
                        "target_user": username
                    }
                    
                    results["success"] += 1
                    results["comments"].append({
                        "post": media.code,
                        "comment": comment_text
                    })
                    count += 1
                    
                    if self.analytics:
                        self.analytics.track_action("comment", True, {
                            "source": "user",
                            "target_user": username
                        })
                    
                    print(f"💬 Commented: '{comment_text}'")
                    
                    delay = random.randint(self.config["delay_min"], self.config["delay_max"])
                    time.sleep(delay)
                    
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(str(e))
            
            self._save_commented_posts()
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
    
    def add_template(self, category, comments):
        """Tambah template comment baru"""
        if category not in self.templates:
            self.templates[category] = []
        
        if isinstance(comments, str):
            comments = [comments]
        
        self.templates[category].extend(comments)
        return {"success": True, "category": category, "total": len(self.templates[category])}
    
    def get_stats(self):
        """Dapatkan statistik auto comment"""
        return {
            "total_commented": len(self.commented_posts),
            "template_categories": list(self.templates.keys()),
            "config": self.config
        }
