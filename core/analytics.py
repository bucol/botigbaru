#!/usr/bin/env python3
"""
Analytics Core - Enhanced Version
Fitur:
- Action Logging (Melacak setiap like/comment individu)
- Daily Stats Snapshot
- Exportable Reports
"""

import os
import json
import logging
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)

class Analytics:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.stats_file = os.path.join(log_dir, "stats.json")
        self.activity_log = os.path.join(log_dir, "activity_log.json")
        
        os.makedirs(log_dir, exist_ok=True)
        
        self.stats = self._load_json(self.stats_file)
        self.activities = self._load_json(self.activity_log)

    def _load_json(self, filepath):
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_json(self, data, filepath):
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Error saving analytics: {e}")

    # =====================================================
    # 🧩 ACTION TRACKING (Real-time)
    # =====================================================
    def track_action(self, action_type, success, metadata=None):
        """
        Melacak satu aksi spesifik.
        Contoh: track_action('like', True, {'target': 'jokowi', 'media_id': 123})
        """
        today = datetime.now().strftime("%Y-%m-%d")
        username = metadata.get("username", "unknown") if metadata else "unknown"
        
        # 1. Update Daily Counter
        if username not in self.stats:
            self.stats[username] = {}
        if today not in self.stats[username]:
            self.stats[username][today] = {
                "likes": 0, "follows": 0, "comments": 0, 
                "stories": 0, "dms": 0, "errors": 0
            }
            
        key = f"{action_type}s" if not action_type.endswith('s') else action_type
        if success:
            if key in self.stats[username][today]:
                self.stats[username][today][key] += 1
        else:
            self.stats[username][today]["errors"] += 1
            
        self._save_json(self.stats, self.stats_file)

        # 2. Log Activity Detail (Optional: Bisa dimatikan kalau file kebesaran)
        if metadata:
            entry = {
                "time": datetime.now().isoformat(),
                "action": action_type,
                "success": success,
                "details": metadata
            }
            if username not in self.activities:
                self.activities[username] = []
            
            self.activities[username].append(entry)
            # Keep only last 1000 logs per user to save space
            if len(self.activities[username]) > 1000:
                self.activities[username] = self.activities[username][-1000:]
                
            self._save_json(self.activities, self.activity_log)

    # =====================================================
    # 📈 STATS SUMMARY
    # =====================================================
    def get_today_stats(self, username=None):
        """Mengambil statistik hari ini"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if username:
            return self.stats.get(username, {}).get(today, {})
        
        # Aggregate all users
        total = defaultdict(int)
        for user, days in self.stats.items():
            if today in days:
                for k, v in days[today].items():
                    total[k] += v
        return dict(total)

    def save_stats(self):
        """Force save"""
        self._save_json(self.stats, self.stats_file)
        self._save_json(self.activities, self.activity_log)

if __name__ == "__main__":
    a = Analytics()
    a.track_action("like", True, {"username": "test_bot", "target": "photo_1"})
    print(a.get_today_stats("test_bot"))