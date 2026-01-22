"""
Target Scraper - Humanized Version
Fitur: Batch Processing, Long Breaks, Incremental Save
"""

import json
import time
import random
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class TargetScraper:
    def __init__(self, client):
        self.client = client
        self.config = {
            "delay_per_user": (1.5, 3.5),
            "batch_size": 40, # Simpan & istirahat setiap 40 user
            "break_time": (60, 180), # Istirahat 1-3 menit antar batch
            "filter_private": False,
            "save_dir": Path("data/scraped")
        }
        self.config["save_dir"].mkdir(parents=True, exist_ok=True)

    def _save_batch(self, users, filename):
        """Simpan progress agar kalau crash data tidak hilang"""
        filepath = self.config["save_dir"] / f"{filename}.json"
        
        # Load existing data if any
        existing_data = []
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
            except: pass
            
        # Merge (hindari duplikat)
        existing_ids = {u['user_id'] for u in existing_data}
        new_users = [u for u in users if u['user_id'] not in existing_ids]
        
        final_data = existing_data + new_users
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
            
        return len(final_data)

    def _extract_user_info(self, user_obj):
        return {
            "user_id": str(user_obj.pk),
            "username": user_obj.username,
            "full_name": user_obj.full_name,
            "is_private": user_obj.is_private,
            "is_verified": user_obj.is_verified,
            "scraped_at": datetime.now().isoformat()
        }

    def scrape_followers(self, target_username, limit=100):
        """Scrape followers dengan etika robot yang sopan"""
        logger.info(f"🕵️ Starting scrape followers of @{target_username} (Target: {limit})")
        
        try:
            target_id = self.client.user_id_from_username(target_username)
            followers = self.client.user_followers(target_id, amount=limit)
            
            scraped_users = []
            count = 0
            
            for uid, user_data in followers.items():
                # Filter (Opsional)
                if self.config['filter_private'] and user_data.is_private:
                    continue
                    
                scraped_users.append(self._extract_user_info(user_data))
                count += 1
                
                # Batch Processing
                if count % self.config['batch_size'] == 0:
                    saved_total = self._save_batch(scraped_users, f"followers_{target_username}")
                    logger.info(f"💾 Saved batch. Total: {saved_total}. Taking a break...")
                    scraped_users = [] # Clear memory buffer
                    time.sleep(random.uniform(*self.config['break_time']))
                else:
                    time.sleep(random.uniform(0.1, 0.5)) # Micro delay

            # Save remaining
            if scraped_users:
                self._save_batch(scraped_users, f"followers_{target_username}")
                
            logger.info(f"✅ Scraping finished. Total collected: {count}")
            return count

        except Exception as e:
            logger.error(f"❌ Scraping error: {e}")
            return 0

    def scrape_by_hashtag(self, hashtag, limit=100):
        """Scrape users from hashtag posts"""
        hashtag = hashtag.lstrip("#")
        logger.info(f"🕵️ Scraping users from #{hashtag}")
        
        try:
            medias = self.client.hashtag_medias_recent(hashtag, amount=limit)
            scraped_users = []
            seen_ids = set()
            
            for i, media in enumerate(medias):
                user = media.user
                if user.pk in seen_ids: continue
                seen_ids.add(user.pk)
                
                scraped_users.append(self._extract_user_info(user))
                
                if len(scraped_users) >= self.config['batch_size']:
                    self._save_batch(scraped_users, f"hashtag_{hashtag}")
                    logger.info(f"💾 Batch saved for #{hashtag}")
                    scraped_users = []
                    time.sleep(random.uniform(*self.config['break_time']))
                
                time.sleep(random.uniform(0.5, 1.5))
                
            if scraped_users:
                self._save_batch(scraped_users, f"hashtag_{hashtag}")
                
            return len(seen_ids)
            
        except Exception as e:
            logger.error(f"❌ Hashtag scrape error: {e}")
            return 0