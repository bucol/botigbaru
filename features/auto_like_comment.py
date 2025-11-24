#!/usr/bin/env python3
"""
Auto Like & Comment
Otomatis like dan komen pada post dengan hashtag atau akun tertentu
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import time
import random

def auto_like_comment(client, username):
    """Auto like dan comment pada post berdasarkan hashtag atau akun"""
    show_separator()
    print(Fore.CYAN + "\n❤️  AUTO LIKE & COMMENT" + Style.RESET_ALL)
    show_separator()

    try:
        print(Fore.YELLOW + "\nPilih mode:" + Style.RESET_ALL)
        print("1. 🔖 Berdasarkan Hashtag")
        print("2. 👤 Berdasarkan Username")
        print("0. ❌ Batal")
        
        choice = input(Fore.MAGENTA + "\nPilih mode (0-2): " + Style.RESET_ALL).strip()

        if choice == '0':
            info_msg("Dibatalkan")
            return
        elif choice == '1':
            auto_by_hashtag(client, username)
        elif choice == '2':
            auto_by_username(client, username)
        else:
            error_msg("Pilihan tidak valid!")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

    input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)

def auto_by_hashtag(client, username):
    """Auto like & comment berdasarkan hashtag"""
    try:
        hashtag = input(Fore.YELLOW + "\nMasukkan hashtag (tanpa #): " + Style.RESET_ALL).strip()
        if not hashtag:
            error_msg("Hashtag tidak boleh kosong!")
            return

        max_posts = input(Fore.YELLOW + "Jumlah post yang akan diproses (default: 10): " + Style.RESET_ALL).strip()
        max_posts = int(max_posts) if max_posts else 10

        do_like = input(Fore.YELLOW + "Auto like? (yes/no): " + Style.RESET_ALL).strip().lower() == "yes"
        do_comment = input(Fore.YELLOW + "Auto comment? (yes/no): " + Style.RESET_ALL).strip().lower() == "yes"

        comments = []
        if do_comment:
            print(Fore.YELLOW + "\nMasukkan komentar (tekan Enter kosong untuk selesai):" + Style.RESET_ALL)
            while True:
                comment = input(Fore.YELLOW + f"Komentar #{len(comments) + 1}: " + Style.RESET_ALL).strip()
                if not comment:
                    break
                comments.append(comment)

            if not comments:
                warning_msg("Tidak ada komentar, skip auto comment")
                do_comment = False

        info_msg(f"Mencari post dengan hashtag #{hashtag}...")
        medias = client.hashtag_medias_recent(hashtag, amount=max_posts)

        processed = 0
        liked = 0
        commented = 0

        for media in medias:
            try:
                processed += 1
                info_msg(f"Proses post {processed}/{len(medias)}")

                if do_like:
                    client.media_like(media.id)
                    liked += 1
                    success_msg(f"✅ Like post dari @{media.user.username}")

                if do_comment and comments:
                    comment_text = random.choice(comments)
                    client.media_comment(media.id, comment_text)
                    commented += 1
                    success_msg(f"✅ Comment: {comment_text}")

                time.sleep(random.randint(3, 7))

            except Exception as e:
                warning_msg(f"Error pada post: {str(e)}")
                continue

        success_msg(f"\n✅ Selesai! Like: {liked}, Comment: {commented}")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def auto_by_username(client, username):
    """Auto like & comment berdasarkan username"""
    try:
        target_username = input(Fore.YELLOW + "\nMasukkan username target: " + Style.RESET_ALL).strip()
        if not target_username:
            error_msg("Username tidak boleh kosong!")
            return

        max_posts = input(Fore.YELLOW + "Jumlah post yang akan diproses (default: 10): " + Style.RESET_ALL).strip()
        max_posts = int(max_posts) if max_posts else 10

        do_like = input(Fore.YELLOW + "Auto like? (yes/no): " + Style.RESET_ALL).strip().lower() == "yes"
        do_comment = input(Fore.YELLOW + "Auto comment? (yes/no): " + Style.RESET_ALL).strip().lower() == "yes"

        comments = []
        if do_comment:
            print(Fore.YELLOW + "\nMasukkan komentar (tekan Enter kosong untuk selesai):" + Style.RESET_ALL)
            while True:
                comment = input(Fore.YELLOW + f"Komentar #{len(comments) + 1}: " + Style.RESET_ALL).strip()
                if not comment:
                    break
                comments.append(comment)

            if not comments:
                warning_msg("Tidak ada komentar, skip auto comment")
                do_comment = False

        info_msg(f"Mencari post dari @{target_username}...")
        user_id = client.user_id_from_username(target_username)
        medias = client.user_medias(user_id, amount=max_posts)

        processed = 0
        liked = 0
        commented = 0

        for media in medias:
            try:
                processed += 1
                info_msg(f"Proses post {processed}/{len(medias)}")

                if do_like:
                    client.media_like(media.id)
                    liked += 1
                    success_msg(f"✅ Like post")

                if do_comment and comments:
                    comment_text = random.choice(comments)
                    client.media_comment(media.id, comment_text)
                    commented += 1
                    success_msg(f"✅ Comment: {comment_text}")

                time.sleep(random.randint(3, 7))

            except Exception as e:
                warning_msg(f"Error pada post: {str(e)}")
                continue

        success_msg(f"\n✅ Selesai! Like: {liked}, Comment: {commented}")

    except Exception as e:
        error_msg(f"Error: {str(e)}")
