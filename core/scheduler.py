import json
import os
import time
import random
from datetime import datetime, timedelta
from collections import deque
from threading import Thread, Lock

class MultiAccountScheduler:
    def __init__(self):
        self.accounts = []
        self.current_index = 0
        self.queue = deque()
        self.lock = Lock()
        self.running = False
        
        self.config = {
            "delay_between_actions": (30, 60),      # detik
            "delay_between_accounts": (300, 600),   # 5-10 menit
            "max_actions_per_account": 50,          # per hari
            "cooldown_after_error": 1800,           # 30 menit
            "daily_reset_hour": 0                    # reset jam 00:00
        }
        
        self.account_stats = {}
        self.schedule_file = "logs/schedule.json"
        
        self._load_schedule()
    
    def _load_schedule(self):
        """Load saved schedule"""
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, "r") as f:
                    data = json.load(f)
                    self.account_stats = data.get("account_stats", {})
            except:
                pass
    
    def _save_schedule(self):
        """Save schedule state"""
        try:
            with open(self.schedule_file, "w") as f:
                json.dump({
                    "account_stats": self.account_stats,
                    "last_updated": datetime.now().isoformat()
                }, f, indent=2)
        except:
            pass
    
    def add_account(self, username: str, password: str, client=None):
        """Add account to rotation pool"""
        account = {
            "username": username,
            "password": password,
            "client": client,
            "logged_in": client is not None
        }
        
        # Initialize stats
        if username not in self.account_stats:
            self.account_stats[username] = {
                "actions_today": 0,
                "last_action": None,
                "last_reset": datetime.now().strftime("%Y-%m-%d"),
                "cooldown_until": None,
                "errors": 0
            }
        
        self.accounts.append(account)
        self._save_schedule()
        return True
    
    def remove_account(self, username: str):
        """Remove account from rotation"""
        self.accounts = [a for a in self.accounts if a["username"] != username]
        if username in self.account_stats:
            del self.account_stats[username]
        self._save_schedule()
    
    def get_next_account(self) -> dict:
        """Get next available account for action"""
        if not self.accounts:
            return None
        
        self._check_daily_reset()
        
        # Find account that can still do actions
        checked = 0
        while checked < len(self.accounts):
            account = self.accounts[self.current_index]
            username = account["username"]
            stats = self.account_stats.get(username, {})
            
            # Check cooldown
            cooldown = stats.get("cooldown_until")
            if cooldown:
                cooldown_time = datetime.fromisoformat(cooldown)
                if datetime.now() < cooldown_time:
                    self.current_index = (self.current_index + 1) % len(self.accounts)
                    checked += 1
                    continue
                else:
                    self.account_stats[username]["cooldown_until"] = None
            
            # Check daily limit
            if stats.get("actions_today", 0) >= self.config["max_actions_per_account"]:
                self.current_index = (self.current_index + 1) % len(self.accounts)
                checked += 1
                continue
            
            # This account is available
            return account
        
        return None  # All accounts exhausted or in cooldown
    
    def rotate_account(self):
        """Move to next account"""
        if self.accounts:
            self.current_index = (self.current_index + 1) % len(self.accounts)
    
    def record_action(self, username: str, success: bool = True):
        """Record an action for account"""
        if username not in self.account_stats:
            return
        
        self.account_stats[username]["actions_today"] += 1
        self.account_stats[username]["last_action"] = datetime.now().isoformat()
        
        if not success:
            self.account_stats[username]["errors"] += 1
            # Set cooldown after error
            if self.account_stats[username]["errors"] >= 3:
                cooldown = datetime.now() + timedelta(seconds=self.config["cooldown_after_error"])
                self.account_stats[username]["cooldown_until"] = cooldown.isoformat()
                self.account_stats[username]["errors"] = 0
        
        self._save_schedule()
    
    def set_cooldown(self, username: str, seconds: int):
        """Set cooldown for account"""
        if username in self.account_stats:
            cooldown = datetime.now() + timedelta(seconds=seconds)
            self.account_stats[username]["cooldown_until"] = cooldown.isoformat()
            self._save_schedule()
    
    def _check_daily_reset(self):
        """Reset daily counters if new day"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        for username, stats in self.account_stats.items():
            if stats.get("last_reset") != today:
                stats["actions_today"] = 0
                stats["last_reset"] = today
                stats["errors"] = 0
        
        self._save_schedule()
    
    def schedule_action(self, action_type: str, target: str, data: dict = None):
        """Add action to queue"""
        with self.lock:
            self.queue.append({
                "type": action_type,
                "target": target,
                "data": data or {},
                "added_at": datetime.now().isoformat(),
                "status": "pending"
            })
    
    def get_queue_status(self) -> dict:
        """Get current queue status"""
        return {
            "queue_length": len(self.queue),
            "accounts_active": len([a for a in self.accounts if a.get("logged_in")]),
            "accounts_total": len(self.accounts),
            "running": self.running
        }
    
    def get_account_status(self, username: str) -> dict:
        """Get status for specific account"""
        stats = self.account_stats.get(username, {})
        account = next((a for a in self.accounts if a["username"] == username), None)
        
        return {
            "username": username,
            "logged_in": account.get("logged_in", False) if account else False,
            "actions_today": stats.get("actions_today", 0),
            "max_actions": self.config["max_actions_per_account"],
            "in_cooldown": bool(stats.get("cooldown_until")),
            "cooldown_until": stats.get("cooldown_until"),
            "last_action": stats.get("last_action"),
            "errors": stats.get("errors", 0)
        }
    
    def get_all_status(self) -> str:
        """Get formatted status of all accounts"""
        status = "📊 *STATUS AKUN*\n\n"
        
        for account in self.accounts:
            username = account["username"]
            acc_status = self.get_account_status(username)
            
            emoji = "🟢" if acc_status["logged_in"] else "🔴"
            if acc_status["in_cooldown"]:
                emoji = "🟡"
            
            status += f"{emoji} @{username}\n"
            status += f"   Actions: {acc_status['actions_today']}/{acc_status['max_actions']}\n"
            if acc_status["in_cooldown"]:
                status += f"   ⏳ Cooldown\n"
            status += "\n"
        
        return status
    
    def get_random_delay(self, delay_type: str = "actions") -> int:
        """Get random delay based on type"""
        if delay_type == "actions":
            min_d, max_d = self.config["delay_between_actions"]
        elif delay_type == "accounts":
            min_d, max_d = self.config["delay_between_accounts"]
        else:
            min_d, max_d = 5, 10
        
        return random.randint(min_d, max_d)
