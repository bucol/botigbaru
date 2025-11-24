#!/usr/bin/env python3
"""
Auto Follow/Unfollow - UPDATED V2
Support multiple usernames, smart limits, anti-detection
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import time
import random

def auto_follow_unfollow(client, username):
    """Menu auto follow/unfollow"""
    show_separator()
    print(Fore.CYAN + "\n👥 AUTO FOLLOW/UNFOLLOW - V2" + Style.RESET_ALL)
    show_separator()

    try:
        print(Fore.YELLOW + "\nPilih aksi:" + Style.RESET_ALL)
        print("1. ➕ Auto Follow (dari hashtag)")
        print("2. ➕ Auto Follow (dari followers akun lain) - SUPPORT MULTIPLE")
        print("3. ➖ Auto Unfollow (yang tidak follow back)")
        print("0. ❌ Batal")
        
        choice = input(Fore.MAGENTA + "\nPilih aksi (0-3): " + Style.RESET_ALL).strip()

        if choice == '0':
            info_msg("Dibatalkan")
            return
        elif choice == '1':
            auto_follow_by_hashtag(client)
        elif choice == '2':
            auto_follow_by_followers_multi(client)  # UPDATED - SUPPORT MULTIPLE
        elif choice == '3':
            auto_unfollow_non_followers(client, username)
        else:
            error_msg("Pilihan tidak valid!")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

    input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)

def auto_follow_by_hashtag(client):
    """Auto follow user dari hashtag"""
    try:
        hashtag = input(Fore.YELLOW + "\nMasukkan hashtag (tanpa #): " + Style.RESET_ALL).strip()
        if not hashtag:
            error_msg("Hashtag tidak boleh kosong!")
            return

        max_users = input(Fore.YELLOW + "Jumlah user yang akan difollow (default: 20, max: 50): " + Style.RESET_ALL).strip()
        max_users = min(int(max_users) if max_users else 20, 50)  # Max 50 untuk anti-detection

        info_msg(f"Mencari user dari hashtag #{hashtag}...")
        medias = client.hashtag_medias_recent(hashtag, amount=max_users * 2)

        followed = 0
        for media in medias:
            if followed >= max_users:
                break

            try:
                client.user_follow(media.user.pk)
                followed += 1
                success_msg(f"✅ Follow @{media.user.username} ({followed}/{max_users})")
                time.sleep(random.randint(5, 15))  # Random delay untuk natural

            except Exception as e:
                warning_msg(f"Error follow @{media.user.username}: {str(e)}")
                continue

        success_msg(f"\n✅ Selesai! Total follow: {followed}/{max_users}")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def auto_follow_by_followers_multi(client):
    """Auto follow dari followers akun lain - SUPPORT MULTIPLE USERNAMES"""
    try:
        print(Fore.YELLOW + "\n📝 Masukkan target username(s):" + Style.RESET_ALL)
        print("  Contoh 1 username: jakarta.keras")
        print("  Contoh multiple: jakarta.keras, factual.id, okemi.id")
        print("  (Pisahkan dengan koma & spasi)\n")
        
        target_input = input(Fore.YELLOW + "Username(s): " + Style.RESET_ALL).strip()
        
        if not target_input:
            error_msg("Username tidak boleh kosong!")
            return

        # Split by comma untuk support multiple
        target_usernames = [u.strip() for u in target_input.split(',')]
        target_usernames = [u for u in target_usernames if u]  # Remove empty strings
        
        if not target_usernames:
            error_msg("Format username tidak valid!")
            return

        max_users = input(Fore.YELLOW + f"Jumlah user yang akan difollow per akun (default: 10, max: 30): " + Style.RESET_ALL).strip()
        max_users = min(int(max_users) if max_users else 10, 30)  # Max 30 per akun

        total_followed_all = 0
        
        # Loop untuk setiap target username
        for target_username in target_usernames:
            try:
                info_msg(f"Processing followers dari @{target_username}...")
                user_id = client.user_id_from_username(target_username)
                followers = client.user_followers(user_id, amount=max_users * 2)

                followed_this_target = 0
                for user_id_follower, user_info in list(followers.items())[:max_users]:
                    try:
                        client.user_follow(user_id_follower)
                        followed_this_target += 1
                        total_followed_all += 1
                        success_msg(f"✅ Follow @{user_info.username} ({followed_this_target}/{max_users}) dari @{target_username}")
                        time.sleep(random.randint(5, 15))

                    except Exception as e:
                        warning_msg(f"Error: {str(e)}")
                        continue

                success_msg(f"✅ Selesai @{target_username}: {followed_this_target} followers")
                time.sleep(random.randint(30, 60))  # Delay antar target username

            except Exception as e:
                error_msg(f"Error process @{target_username}: {str(e)}")
                continue

        success_msg(f"\n✅ TOTAL FOLLOW SEMUA AKUN: {total_followed_all} users")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def auto_unfollow_non_followers(client, username):
    """Auto unfollow yang tidak follow back"""
    try:
        confirm = input(Fore.RED + "\n⚠️  Unfollow semua yang tidak follow back? (yes/no): " + Style.RESET_ALL).strip().lower()
        if confirm != "yes":
            info_msg("Dibatalkan")
            return

        max_unfollow = input(Fore.YELLOW + "Max unfollow per session (default: 20, max: 50): " + Style.RESET_ALL).strip()
        max_unfollow = min(int(max_unfollow) if max_unfollow else 20, 50)  # Anti-detection limit

        info_msg("Mengambil daftar following dan followers...")
        user_id = client.user_id_from_username(username)
        
        following = client.user_following(user_id)
        followers = client.user_followers(user_id)
        
        follower_ids = set(followers.keys())
        non_followers = [uid for uid in following.keys() if uid not in follower_ids]

        if not non_followers:
            success_msg("✅ Semua following sudah follow back!")
            return

        info_msg(f"Ditemukan {len(non_followers)} user yang tidak follow back")
        print(Fore.YELLOW + f"Akan unfollow maksimal {max_unfollow} (dari {len(non_followers)})" + Style.RESET_ALL)
        
        confirm_unfollow = input(Fore.RED + "\nLanjutkan? (yes/no): " + Style.RESET_ALL).strip().lower()
        if confirm_unfollow != "yes":
            info_msg("Dibatalkan")
            return
        
        unfollowed = 0
        for user_id_unfollow in non_followers:
            if unfollowed >= max_unfollow:
                break

            try:
                user_info = following[user_id_unfollow]
                client.user_unfollow(user_id_unfollow)
                unfollowed += 1
                success_msg(f"✅ Unfollow @{user_info.username} ({unfollowed}/{max_unfollow})")
                time.sleep(random.randint(5, 15))  # Random delay

            except Exception as e:
                warning_msg(f"Error: {str(e)}")
                continue

        success_msg(f"\n✅ Selesai! Total unfollow: {unfollowed}/{len(non_followers)}")

    except Exception as e:
        error_msg(f"Error: {str(e)}")
