#!/usr/bin/env python3
"""
Login Activity Monitor
Pantau login activity & detect suspicious activity
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import json
import os
from datetime import datetime, timedelta

class LoginMonitor:
    def __init__(self):
        self.log_file = "data/login_activity.json"
        self.load_logs()

    def load_logs(self):
        """Load login logs"""
        os.makedirs("data", exist_ok=True)

        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.logs = json.load(f)
            except:
                self.logs = {}
        else:
            self.logs = {}

    def save_logs(self):
        """Save login logs"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.logs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            warning_msg(f"Error save logs: {str(e)}")

    def log_login(self, username, device_info="Web", location="Unknown"):
        """Log login activity"""
        try:
            if username not in self.logs:
                self.logs[username] = []

            login_entry = {
                'timestamp': datetime.now().isoformat(),
                'device': device_info,
                'location': location,
                'status': 'success'
            }

            self.logs[username].append(login_entry)

            # Keep only last 100 logins per account
            if len(self.logs[username]) > 100:
                self.logs[username] = self.logs[username][-100:]

            self.save_logs()

        except Exception as e:
            warning_msg(f"Error log login: {str(e)}")

    def check_suspicious_activity(self, username, threshold=5):
        """Check suspicious activity (multiple failed logins)"""
        try:
            if username not in self.logs:
                return False

            # Check last 1 hour
            now = datetime.now()
            one_hour_ago = now - timedelta(hours=1)

            recent_logins = [
                log for log in self.logs[username]
                if datetime.fromisoformat(log['timestamp']) > one_hour_ago
            ]

            # Count failed attempts
            failed_count = len([l for l in recent_logins if l['status'] == 'failed'])

            if failed_count >= threshold:
                return True

            return False

        except Exception as e:
            warning_msg(f"Error check activity: {str(e)}")
            return False

    def get_login_history(self, username, limit=20):
        """Get login history untuk akun"""
        try:
            if username not in self.logs:
                return []

            return self.logs[username][-limit:]

        except Exception as e:
            warning_msg(f"Error get history: {str(e)}")
            return []

    def display_login_history(self, username):
        """Display login history"""
        history = self.get_login_history(username)

        if not history:
            warning_msg("No login history")
            return

        show_separator()
        print(Fore.CYAN + f"\n📋 LOGIN HISTORY - @{username}" + Style.RESET_ALL)
        show_separator()

        for i, log in enumerate(history[::-1], 1):  # Reverse untuk newest first
            timestamp = log['timestamp'][:16]  # YYYY-MM-DD HH:MM
            device = log['device']
            location = log['location']
            status = Fore.GREEN + "✅" if log['status'] == 'success' else Fore.RED + "❌"

            print(f"\n{i}. {status}{Style.RESET_ALL}")
            print(f"   Time: {timestamp}")
            print(f"   Device: {device}")
            print(f"   Location: {location}")

    def export_login_logs(self, username):
        """Export login logs to CSV"""
        try:
            history = self.get_login_history(username, limit=None)

            if not history:
                warning_msg("No logs to export")
                return

            filename = f"data/login_logs_{username}_{int(__import__('time').time())}.csv"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write("Timestamp,Device,Location,Status\n")

                for log in history:
                    timestamp = log['timestamp']
                    device = log['device']
                    location = log['location']
                    status = log['status']

                    f.write(f"{timestamp},{device},{location},{status}\n")

            success_msg(f"✅ Exported to {filename}")

        except Exception as e:
            error_msg(f"Error export: {str(e)}")

    def run_monitor_menu(self, username):
        """Menu login monitor"""
        show_separator()
        print(Fore.CYAN + "\n🔐 LOGIN ACTIVITY MONITOR" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nPilih aksi:" + Style.RESET_ALL)
            print("1. 📋 View login history")
            print("2. 🔍 Check suspicious activity")
            print("3. 📊 Export logs")
            print("0. ❌ Batal")

            choice = input(Fore.MAGENTA + "\nPilih (0-3): " + Style.RESET_ALL).strip()

            if choice == '0':
                return

            elif choice == '1':
                self.display_login_history(username)

            elif choice == '2':
                if self.check_suspicious_activity(username):
                    warning_msg("⚠️  SUSPICIOUS ACTIVITY DETECTED!")
                    print("Multiple failed login attempts detected in last hour")
                else:
                    success_msg("✅ No suspicious activity detected")

            elif choice == '3':
                self.export_login_logs(username)

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def login_monitor_menu(username):
    """Menu wrapper"""
    monitor = LoginMonitor()
    monitor.run_monitor_menu(username)
