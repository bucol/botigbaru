#!/usr/bin/env python3
"""
Notification System
Monitor followers baru, DM, comments, likes
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import json
import os
from datetime import datetime
import time
import threading

class NotificationSystem:
    def __init__(self, client):
        self.client = client
        self.notifications_file = "data/notifications_log.json"
        self.config_file = "data/notifications_config.json"
        self.load_config()

    def load_config(self):
        """Load notification config"""
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
        """Default notification settings"""
        return {
            'notify_followers': True,
            'notify_dm': True,
            'notify_comments': True,
            'notify_likes': True,
            'check_interval': 300,  # seconds
            'sound_enabled': False,
            'max_notifications': 100
        }

    def save_config(self):
        """Save config"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            warning_msg(f"Error save config: {str(e)}")

    def add_notification(self, notification_type, data):
        """Tambah notification ke log"""
        try:
            notifications = []

            if os.path.exists(self.notifications_file):
                try:
                    with open(self.notifications_file, 'r', encoding='utf-8') as f:
                        notifications = json.load(f)
                except:
                    notifications = []

            notification = {
                'type': notification_type,
                'data': data,
                'timestamp': datetime.now().isoformat(),
                'read': False
            }

            notifications.append(notification)

            # Keep only last N notifications
            if len(notifications) > self.config['max_notifications']:
                notifications = notifications[-self.config['max_notifications']:]

            with open(self.notifications_file, 'w', encoding='utf-8') as f:
                json.dump(notifications, f, indent=4, ensure_ascii=False)

            return notification

        except Exception as e:
            warning_msg(f"Error add notification: {str(e)}")
            return None

    def check_new_followers(self, username, prev_followers):
        """Check followers baru"""
        try:
            user_info = self.client.user_info_by_username(username)
            current_followers = user_info.follower_count

            if current_followers > prev_followers:
                new_followers = current_followers - prev_followers

                notification = {
                    'username': username,
                    'new_followers': new_followers,
                    'total': current_followers
                }

                self.add_notification('new_followers', notification)

                print(Fore.GREEN + f"\n👥 NEW FOLLOWERS: +{new_followers}" + Style.RESET_ALL)
                print(f"   Total: {current_followers}")

                return current_followers

            return prev_followers

        except Exception as e:
            warning_msg(f"Error check followers: {str(e)}")
            return prev_followers

    def check_new_dm(self, username):
        """Check DM masuk"""
        try:
            inbox = self.client.direct_threads(amount=10)

            for thread in inbox:
                # Get latest message
                if thread.messages:
                    latest = thread.messages[0]

                    if latest.user_id != self.client.user_id:
                        notification = {
                            'from': thread.users[0].username if thread.users else 'Unknown',
                            'preview': latest.text[:50] if latest.text else '[Media]',
                            'thread_id': thread.id
                        }

                        self.add_notification('new_dm', notification)

                        print(Fore.CYAN + f"\n💬 NEW DM from @{notification['from']}" + Style.RESET_ALL)
                        print(f"   {notification['preview']}")

        except Exception as e:
            warning_msg(f"Error check DM: {str(e)}")

    def display_notifications(self):
        """Display notification history"""
        try:
            if not os.path.exists(self.notifications_file):
                warning_msg("No notifications yet")
                return

            with open(self.notifications_file, 'r', encoding='utf-8') as f:
                notifications = json.load(f)

            if not notifications:
                warning_msg("No notifications")
                return

            show_separator()
            print(Fore.CYAN + "\n🔔 NOTIFICATION HISTORY" + Style.RESET_ALL)
            show_separator()

            for i, notif in enumerate(notifications[-20:], 1):  # Show last 20
                notif_type = notif['type'].upper()
                timestamp = notif['timestamp'][:10]

                print(f"\n{i}. [{notif_type}] {timestamp}")

                if notif['type'] == 'new_followers':
                    print(f"   +{notif['data']['new_followers']} followers")
                elif notif['type'] == 'new_dm':
                    print(f"   From: @{notif['data']['from']}")
                    print(f"   {notif['data']['preview']}")

        except Exception as e:
            error_msg(f"Error display notifications: {str(e)}")

    def run_monitor(self, username, duration=600):
        """Run background monitor"""
        try:
            info_msg(f"Starting notification monitor ({duration}s)...")
            print(Fore.YELLOW + "Press Ctrl+C to stop" + Style.RESET_ALL)

            # Get initial follower count
            user_info = self.client.user_info_by_username(username)
            prev_followers = user_info.follower_count

            start_time = time.time()

            while time.time() - start_time < duration:
                try:
                    if self.config['notify_followers']:
                        prev_followers = self.check_new_followers(username, prev_followers)

                    if self.config['notify_dm']:
                        self.check_new_dm(username)

                    time.sleep(self.config['check_interval'])

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    warning_msg(f"Monitor error: {str(e)}")
                    continue

            success_msg("Monitor stopped")

        except Exception as e:
            error_msg(f"Error run monitor: {str(e)}")

    def run_notification_menu(self, username):
        """Menu notification system"""
        show_separator()
        print(Fore.CYAN + "\n🔔 NOTIFICATION SYSTEM" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nPilih aksi:" + Style.RESET_ALL)
            print("1. 📋 View notification history")
            print("2. ⚙️  Update notification settings")
            print("3. 🔄 Start real-time monitor")
            print("0. ❌ Batal")

            choice = input(Fore.MAGENTA + "\nPilih (0-3): " + Style.RESET_ALL).strip()

            if choice == '0':
                return

            elif choice == '1':
                self.display_notifications()

            elif choice == '2':
                print(Fore.YELLOW + "\nCurrent settings:" + Style.RESET_ALL)
                print(f"  Followers: {'✅' if self.config['notify_followers'] else '❌'}")
                print(f"  DM: {'✅' if self.config['notify_dm'] else '❌'}")
                print(f"  Comments: {'✅' if self.config['notify_comments'] else '❌'}")
                print(f"  Likes: {'✅' if self.config['notify_likes'] else '❌'}")

            elif choice == '3':
                duration = input(Fore.YELLOW + "Monitor duration (seconds, default: 600): " + Style.RESET_ALL).strip()
                duration = int(duration) if duration else 600

                self.run_monitor(username, duration)

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def notification_system_menu(client, username):
    """Menu wrapper"""
    notif = NotificationSystem(client)
    notif.run_notification_menu(username)
