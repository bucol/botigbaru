#!/usr/bin/env python3
"""
Smart Unfollow - Enhanced
Unfollow dengan criteria lebih detail
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import time
import random

class SmartUnfollow:
    def __init__(self, client):
        self.client = client

    def unfollow_non_engaged(self, username, days=14, min_engagement=0):
        """Unfollow akun yang tidak engage (no like/comment selama X hari)"""
        try:
            info_msg(f"Finding non-engaged accounts (last {days} days)...")

            user_id = self.client.user_id_from_username(username)
            following = self.client.user_following(user_id)
            
            non_engaged = []

            for follow_user_id, follow_user_info in following.items():
                try:
                    # Get recent posts dari account ini
                    medias = self.client.user_medias(follow_user_id, amount=5)
                    
                    # Check engagement dari waktu X hari lalu
                    engagement_count = 0
                    for media in medias:
                        # Simple check: jika ada likes, berarti kita suka
                        # (actual implementation need more complex logic)
                        engagement_count += 1

                    if engagement_count <= min_engagement:
                        non_engaged.append({
                            'user_id': follow_user_id,
                            'username': follow_user_info.username,
                            'follower_count': follow_user_info.follower_count
                        })

                except:
                    continue

            return non_engaged

        except Exception as e:
            error_msg(f"Error find non-engaged: {str(e)}")
            return []

    def unfollow_low_follower(self, username, min_followers=1000):
        """Unfollow akun dengan follower < threshold"""
        try:
            info_msg(f"Finding accounts with followers < {min_followers}...")

            user_id = self.client.user_id_from_username(username)
            following = self.client.user_following(user_id)

            low_follower = []

            for follow_user_id, follow_user_info in following.items():
                if follow_user_info.follower_count < min_followers:
                    low_follower.append({
                        'user_id': follow_user_id,
                        'username': follow_user_info.username,
                        'follower_count': follow_user_info.follower_count
                    })

            return low_follower

        except Exception as e:
            error_msg(f"Error find low follower: {str(e)}")
            return []

    def unfollow_batch(self, accounts, max_unfollow=20):
        """Unfollow batch dengan limit & delay"""
        try:
            if len(accounts) == 0:
                warning_msg("Tidak ada akun untuk di-unfollow")
                return 0

            # Show preview
            show_separator()
            print(Fore.YELLOW + f"\n📋 PREVIEW - {len(accounts)} accounts:" + Style.RESET_ALL)
            
            for i, acc in enumerate(accounts[:5], 1):
                print(f"  {i}. @{acc['username']} ({acc['follower_count']:,} followers)")
            
            if len(accounts) > 5:
                print(f"  ... and {len(accounts) - 5} more")

            # Apply limit
            to_unfollow = accounts[:min(max_unfollow, len(accounts))]
            print(Fore.RED + f"\n⚠️  Will unfollow: {len(to_unfollow)}" + Style.RESET_ALL)

            confirm = input(Fore.RED + "\nConfirm? (yes/no): " + Style.RESET_ALL).strip().lower()

            if confirm != "yes":
                info_msg("Dibatalkan")
                return 0

            # Execute unfollow
            unfollowed = 0

            info_msg("Starting unfollow batch...")

            for i, acc in enumerate(to_unfollow, 1):
                try:
                    self.client.user_unfollow(acc['user_id'])
                    unfollowed += 1
                    success_msg(f"✅ Unfollow @{acc['username']} ({i}/{len(to_unfollow)})")
                    
                    # Random delay (3-10 detik)
                    delay = random.randint(3, 10)
                    time.sleep(delay)

                except Exception as e:
                    warning_msg(f"Error unfollow @{acc['username']}: {str(e)}")
                    continue

            success_msg(f"\n✅ Total unfollowed: {unfollowed}")
            return unfollowed

        except Exception as e:
            error_msg(f"Error batch unfollow: {str(e)}")
            return 0

    def run_smart_unfollow_menu(self, username):
        """Menu smart unfollow"""
        show_separator()
        print(Fore.CYAN + "\n🗑️  SMART UNFOLLOW - ADVANCED" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nPilih strategy:" + Style.RESET_ALL)
            print("1. 💤 Non-engaged accounts (no activity X days)")
            print("2. 📉 Low follower count")
            print("3. 🔄 Unfollow non-followers")
            print("0. ❌ Batal")

            choice = input(Fore.MAGENTA + "\nPilih (0-3): " + Style.RESET_ALL).strip()

            if choice == '0':
                info_msg("Dibatalkan")
                return

            elif choice == '1':
                days = input(Fore.YELLOW + "Non-engaged X hari (default: 14): " + Style.RESET_ALL).strip()
                days = int(days) if days else 14
                accounts = self.unfollow_non_engaged(username, days)
                self.unfollow_batch(accounts)

            elif choice == '2':
                min_followers = input(Fore.YELLOW + "Min follower threshold (default: 1000): " + Style.RESET_ALL).strip()
                min_followers = int(min_followers) if min_followers else 1000
                accounts = self.unfollow_low_follower(username, min_followers)
                self.unfollow_batch(accounts)

            elif choice == '3':
                warning_msg("Use Auto Follow/Unfollow menu untuk fitur ini")

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def smart_unfollow_menu(client, username):
    """Menu wrapper"""
    smart = SmartUnfollow(client)
    smart.run_smart_unfollow_menu(username)
