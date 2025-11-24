#!/usr/bin/env python3
"""
Anti-Detection System - Global
Lindungi bot dari detection & shadowban
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import json
import os
from datetime import datetime, timedelta

class AntiDetectionManager:
    def __init__(self):
        self.config_file = "data/anti_detection_config.json"
        self.action_log_file = "data/action_logs.json"
        self.load_config()

    def load_config(self):
        """Load anti-detection config"""
        os.makedirs("data", exist_ok=True)
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except:
                self.config = self.get_default_config()
        else:
            self.config = self.get_default_config()
            self.save_config()

    def get_default_config(self):
        """Default anti-detection settings"""
        return {
            'max_follow_per_day': 50,
            'max_like_per_day': 100,
            'max_comment_per_day': 30,
            'max_dm_per_day': 20,
            'min_delay_between_actions': 3,  # seconds
            'max_delay_between_actions': 15,  # seconds
            'enable_random_breaks': True,
            'break_every_n_actions': 20,
            'break_duration': 300,  # seconds
            'use_proxy': False,
            'proxy_list': [],
            'shadowban_check_enabled': True
        }

    def save_config(self):
        """Save config ke file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            error_msg(f"Error save config: {str(e)}")

    def log_action(self, username, action_type, action_count=1):
        """Log setiap action untuk tracking"""
        try:
            logs = {}
            if os.path.exists(self.action_log_file):
                with open(self.action_log_file, 'r', encoding='utf-8') as f:
                    logs = json.load(f)
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if today not in logs:
                logs[today] = {}
            
            if username not in logs[today]:
                logs[today][username] = {}
            
            if action_type not in logs[today][username]:
                logs[today][username][action_type] = 0
            
            logs[today][username][action_type] += action_count
            
            with open(self.action_log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=4, ensure_ascii=False)
        
        except Exception as e:
            warning_msg(f"Error log action: {str(e)}")

    def check_daily_limits(self, username, action_type):
        """Check apakah sudah exceed daily limit"""
        try:
            if not os.path.exists(self.action_log_file):
                return True

            with open(self.action_log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if today not in logs or username not in logs[today]:
                return True
            
            action_count = logs[today][username].get(action_type, 0)
            limit_key = f"max_{action_type}_per_day"
            limit = self.config.get(limit_key, 999)
            
            return action_count < limit
        
        except:
            return True

    def get_action_count_today(self, username, action_type):
        """Get jumlah action hari ini"""
        try:
            if not os.path.exists(self.action_log_file):
                return 0

            with open(self.action_log_file, 'r', encoding='utf-8') as f:
                logs = json.load(f)
            
            today = datetime.now().strftime("%Y-%m-%d")
            
            if today not in logs or username not in logs[today]:
                return 0
            
            return logs[today][username].get(action_type, 0)
        
        except:
            return 0

    def get_remaining_actions(self, username, action_type):
        """Get sisa action untuk hari ini"""
        count_today = self.get_action_count_today(username, action_type)
        limit_key = f"max_{action_type}_per_day"
        limit = self.config.get(limit_key, 999)
        
        return max(0, limit - count_today)

    def display_config(self):
        """Display current config"""
        show_separator()
        print(Fore.CYAN + "\n🕵️ ANTI-DETECTION CONFIG" + Style.RESET_ALL)
        show_separator()

        print(Fore.YELLOW + "\n📊 DAILY LIMITS:" + Style.RESET_ALL)
        print(f"  Follow: {self.config['max_follow_per_day']}/day")
        print(f"  Like: {self.config['max_like_per_day']}/day")
        print(f"  Comment: {self.config['max_comment_per_day']}/day")
        print(f"  DM: {self.config['max_dm_per_day']}/day")

        print(Fore.YELLOW + "\n⏱️  DELAYS:" + Style.RESET_ALL)
        print(f"  Min: {self.config['min_delay_between_actions']}s")
        print(f"  Max: {self.config['max_delay_between_actions']}s")

        print(Fore.YELLOW + "\n🔧 FEATURES:" + Style.RESET_ALL)
        print(f"  Random Breaks: {'✅' if self.config['enable_random_breaks'] else '❌'}")
        print(f"  Break every {self.config['break_every_n_actions']} actions ({self.config['break_duration']}s)")
        print(f"  Shadowban Check: {'✅' if self.config['shadowban_check_enabled'] else '❌'}")

    def update_config(self):
        """Interactive config update"""
        show_separator()
        print(Fore.CYAN + "\n⚙️  UPDATE ANTI-DETECTION CONFIG" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nPilih setting untuk update:" + Style.RESET_ALL)
            print("1. Max follow/day")
            print("2. Max like/day")
            print("3. Max comment/day")
            print("4. Max DM/day")
            print("5. Min delay")
            print("6. Max delay")
            print("7. Enable random breaks")
            print("0. Kembali")

            choice = input(Fore.MAGENTA + "\nPilih (0-7): " + Style.RESET_ALL).strip()

            if choice == '0':
                return

            elif choice == '1':
                value = input(Fore.YELLOW + "Max follow/day (current: {0}): ".format(self.config['max_follow_per_day']) + Style.RESET_ALL).strip()
                self.config['max_follow_per_day'] = int(value)

            elif choice == '2':
                value = input(Fore.YELLOW + "Max like/day (current: {0}): ".format(self.config['max_like_per_day']) + Style.RESET_ALL).strip()
                self.config['max_like_per_day'] = int(value)

            elif choice == '3':
                value = input(Fore.YELLOW + "Max comment/day (current: {0}): ".format(self.config['max_comment_per_day']) + Style.RESET_ALL).strip()
                self.config['max_comment_per_day'] = int(value)

            elif choice == '4':
                value = input(Fore.YELLOW + "Max DM/day (current: {0}): ".format(self.config['max_dm_per_day']) + Style.RESET_ALL).strip()
                self.config['max_dm_per_day'] = int(value)

            elif choice == '5':
                value = input(Fore.YELLOW + "Min delay (current: {0}s): ".format(self.config['min_delay_between_actions']) + Style.RESET_ALL).strip()
                self.config['min_delay_between_actions'] = int(value)

            elif choice == '6':
                value = input(Fore.YELLOW + "Max delay (current: {0}s): ".format(self.config['max_delay_between_actions']) + Style.RESET_ALL).strip()
                self.config['max_delay_between_actions'] = int(value)

            elif choice == '7':
                value = input(Fore.YELLOW + "Enable random breaks? (yes/no): " + Style.RESET_ALL).strip().lower()
                self.config['enable_random_breaks'] = value == "yes"

            self.save_config()
            success_msg("✅ Config updated!")

        except Exception as e:
            error_msg(f"Error: {str(e)}")

    def run_anti_detection_menu(self):
        """Menu anti-detection"""
        show_separator()
        print(Fore.CYAN + "\n🕵️ ANTI-DETECTION SYSTEM" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nPilih aksi:" + Style.RESET_ALL)
            print("1. 📊 View current config")
            print("2. ⚙️  Update config")
            print("3. 📋 View action logs")
            print("0. ❌ Batal")

            choice = input(Fore.MAGENTA + "\nPilih (0-3): " + Style.RESET_ALL).strip()

            if choice == '0':
                return

            elif choice == '1':
                self.display_config()

            elif choice == '2':
                self.update_config()

            elif choice == '3':
                if os.path.exists(self.action_log_file):
                    with open(self.action_log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                    
                    show_separator()
                    print(Fore.CYAN + "\n📋 ACTION LOGS (Today)" + Style.RESET_ALL)
                    show_separator()

                    today = datetime.now().strftime("%Y-%m-%d")
                    
                    if today in logs:
                        for username, actions in logs[today].items():
                            print(Fore.YELLOW + f"\n@{username}:" + Style.RESET_ALL)
                            for action, count in actions.items():
                                print(f"  {action}: {count}")
                    else:
                        info_msg("No actions today")
                else:
                    warning_msg("No action logs yet")

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def anti_detection_menu():
    """Menu wrapper"""
    anti_det = AntiDetectionManager()
    anti_det.run_anti_detection_menu()
