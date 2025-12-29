import json
import os
from datetime import datetime, timedelta
from collections import defaultdict

class Analytics:
    def __init__(self):
        self.log_dir = "logs"
        self.stats_file = "logs/stats.json"
        self.stats = self._load_stats()
        
        os.makedirs(self.log_dir, exist_ok=True)
    
    def _load_stats(self) -> dict:
        """Load existing stats"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {
            "total": {"likes": 0, "follows": 0, "unfollows": 0, "comments": 0, "dms": 0, "story_views": 0},
            "daily": {},
            "accounts": {}
        }
    
    def _save_stats(self):
        """Save stats to file"""
        try:
            with open(self.stats_file, "w") as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            print(f"Stats save error: {e}")
    
    def track(self, action: str, username: str = "unknown", target: str = "", success: bool = True):
        """Track an action"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Initialize daily stats if needed
        if today not in self.stats["daily"]:
            self.stats["daily"][today] = {
                "likes": 0, "follows": 0, "unfollows": 0,
                "comments": 0, "dms": 0, "story_views": 0,
                "errors": 0
            }
        
        # Initialize account stats if needed
        if username not in self.stats["accounts"]:
            self.stats["accounts"][username] = {
                "likes": 0, "follows": 0, "unfollows": 0,
                "comments": 0, "dms": 0, "story_views": 0,
                "last_active": None
            }
        
        # Update stats
        if success and action in self.stats["total"]:
            self.stats["total"][action] += 1
            self.stats["daily"][today][action] += 1
            self.stats["accounts"][username][action] += 1
            self.stats["accounts"][username]["last_active"] = datetime.now().isoformat()
        elif not success:
            self.stats["daily"][today]["errors"] += 1
        
        # Log the action
        self._log_action(action, username, target, success)
        self._save_stats()
    
    def _log_action(self, action: str, username: str, target: str, success: bool):
        """Log action to daily log file"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "username": username,
            "target": target,
            "success": success
        }
        
        log_file = os.path.join(self.log_dir, f"actions_{datetime.now().strftime('%Y%m%d')}.log")
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except:
            pass
    
    def get_daily_stats(self, date: str = None) -> dict:
        """Get stats for a specific date"""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        return self.stats["daily"].get(date, {})
    
    def get_weekly_stats(self) -> dict:
        """Get stats for the last 7 days"""
        weekly = {
            "likes": 0, "follows": 0, "unfollows": 0,
            "comments": 0, "dms": 0, "story_views": 0,
            "errors": 0, "days_active": 0
        }
        
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            if date in self.stats["daily"]:
                weekly["days_active"] += 1
                for key in ["likes", "follows", "unfollows", "comments", "dms", "story_views", "errors"]:
                    weekly[key] += self.stats["daily"][date].get(key, 0)
        
        return weekly
    
    def get_account_stats(self, username: str) -> dict:
        """Get stats for specific account"""
        return self.stats["accounts"].get(username, {})
    
    def format_daily_report(self) -> str:
        """Format daily stats for Telegram"""
        today = datetime.now().strftime("%Y-%m-%d")
        stats = self.get_daily_stats(today)
        
        if not stats:
            return "📊 *LAPORAN HARIAN*\n\nBelum ada aktivitas hari ini."
        
        report = f"""📊 *LAPORAN HARIAN*
📅 {today}

━━━━━━━━━━━━━━━━━━
❤️ Likes: {stats.get('likes', 0)}
👥 Follows: {stats.get('follows', 0)}
👋 Unfollows: {stats.get('unfollows', 0)}
💬 Comments: {stats.get('comments', 0)}
📩 DMs: {stats.get('dms', 0)}
👁️ Story Views: {stats.get('story_views', 0)}
━━━━━━━━━━━━━━━━━━
❌ Errors: {stats.get('errors', 0)}
"""
        return report
    
    def format_weekly_report(self) -> str:
        """Format weekly stats for Telegram"""
        stats = self.get_weekly_stats()
        
        report = f"""📊 *LAPORAN MINGGUAN*
📅 7 Hari Terakhir

━━━━━━━━━━━━━━━━━━
❤️ Total Likes: {stats['likes']}
👥 Total Follows: {stats['follows']}
👋 Total Unfollows: {stats['unfollows']}
💬 Total Comments: {stats['comments']}
📩 Total DMs: {stats['dms']}
👁️ Total Story Views: {stats['story_views']}
━━━━━━━━━━━━━━━━━━
📆 Hari Aktif: {stats['days_active']}/7
❌ Total Errors: {stats['errors']}
"""
        return report
    
    def format_total_report(self) -> str:
        """Format all-time stats for Telegram"""
        stats = self.stats["total"]
        
        report = f"""📊 *STATISTIK KESELURUHAN*

━━━━━━━━━━━━━━━━━━
❤️ Total Likes: {stats.get('likes', 0)}
👥 Total Follows: {stats.get('follows', 0)}
👋 Total Unfollows: {stats.get('unfollows', 0)}
💬 Total Comments: {stats.get('comments', 0)}
📩 Total DMs: {stats.get('dms', 0)}
👁️ Total Story Views: {stats.get('story_views', 0)}
━━━━━━━━━━━━━━━━━━
👤 Total Akun: {len(self.stats['accounts'])}
"""
        return report
