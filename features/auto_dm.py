#!/usr/bin/env python3
"""
Auto DM
Kirim pesan langsung otomatis ke followers baru atau berdasarkan trigger tertentu
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import time
import random

def auto_dm(client, username):
    """Menu auto DM"""
    show_separator()
    print(Fore.CYAN + "\n💬 AUTO DM (DIRECT MESSAGE)" + Style.RESET_ALL)
    show_separator()

    try:
        print(Fore.YELLOW + "\nPilih target:" + Style.RESET_ALL)
        print("1. 👥 Kirim ke Semua Followers")
        print("2. 🆕 Kirim ke Followers Baru (input manual)")
        print("3. 📋 Kirim ke List Username")
        print("0. ❌ Batal")
        
        choice = input(Fore.MAGENTA + "\nPilih target (0-3): " + Style.RESET_ALL).strip()

        if choice == '0':
            info_msg("Dibatalkan")
            return
        elif choice == '1':
            dm_to_all_followers(client, username)
        elif choice == '2':
            dm_to_new_followers(client)
        elif choice == '3':
            dm_to_username_list(client)
        else:
            error_msg("Pilihan tidak valid!")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

    input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)

def dm_to_all_followers(client, username):
    """Kirim DM ke semua followers"""
    try:
        message = input(Fore.YELLOW + "\nMasukkan pesan: " + Style.RESET_ALL).strip()
        if not message:
            error_msg("Pesan tidak boleh kosong!")
            return

        max_send = input(Fore.YELLOW + "Jumlah maksimal DM (default: 50): " + Style.RESET_ALL).strip()
        max_send = int(max_send) if max_send else 50

        confirm = input(Fore.RED + f"\n⚠️  Kirim DM ke {max_send} followers? (yes/no): " + Style.RESET_ALL).strip().lower()
        if confirm != "yes":
            info_msg("Dibatalkan")
            return

        info_msg("Mengambil daftar followers...")
        user_id = client.user_id_from_username(username)
        followers = client.user_followers(user_id, amount=max_send)

        sent = 0
        for user_id, user_info in list(followers.items())[:max_send]:
            try:
                client.direct_send(message, [user_id])
                sent += 1
                success_msg(f"✅ DM terkirim ke @{user_info.username} ({sent}/{max_send})")
                time.sleep(random.randint(10, 20))

            except Exception as e:
                warning_msg(f"Error: {str(e)}")
                continue

        success_msg(f"\n✅ Selesai! Total DM terkirim: {sent}")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def dm_to_new_followers(client):
    """Kirim DM ke followers baru (input manual username)"""
    try:
        message = input(Fore.YELLOW + "\nMasukkan pesan: " + Style.RESET_ALL).strip()
        if not message:
            error_msg("Pesan tidak boleh kosong!")
            return

        print(Fore.YELLOW + "\nMasukkan username followers baru (tekan Enter kosong untuk selesai):" + Style.RESET_ALL)
        usernames = []
        while True:
            uname = input(Fore.YELLOW + f"Username #{len(usernames) + 1}: " + Style.RESET_ALL).strip()
            if not uname:
                break
            usernames.append(uname)

        if not usernames:
            error_msg("Tidak ada username yang diinput!")
            return

        sent = 0
        for uname in usernames:
            try:
                user_id = client.user_id_from_username(uname)
                client.direct_send(message, [user_id])
                sent += 1
                success_msg(f"✅ DM terkirim ke @{uname} ({sent}/{len(usernames)})")
                time.sleep(random.randint(10, 20))

            except Exception as e:
                warning_msg(f"Error kirim ke @{uname}: {str(e)}")
                continue

        success_msg(f"\n✅ Selesai! Total DM terkirim: {sent}")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def dm_to_username_list(client):
    """Kirim DM ke list username"""
    try:
        message = input(Fore.YELLOW + "\nMasukkan pesan: " + Style.RESET_ALL).strip()
        if not message:
            error_msg("Pesan tidak boleh kosong!")
            return

        print(Fore.YELLOW + "\nMasukkan username (tekan Enter kosong untuk selesai):" + Style.RESET_ALL)
        usernames = []
        while True:
            uname = input(Fore.YELLOW + f"Username #{len(usernames) + 1}: " + Style.RESET_ALL).strip()
            if not uname:
                break
            usernames.append(uname)

        if not usernames:
            error_msg("Tidak ada username yang diinput!")
            return

        sent = 0
        for uname in usernames:
            try:
                user_id = client.user_id_from_username(uname)
                client.direct_send(message, [user_id])
                sent += 1
                success_msg(f"✅ DM terkirim ke @{uname} ({sent}/{len(usernames)})")
                time.sleep(random.randint(10, 20))

            except Exception as e:
                warning_msg(f"Error kirim ke @{uname}: {str(e)}")
                continue

        success_msg(f"\n✅ Selesai! Total DM terkirim: {sent}")

    except Exception as e:
        error_msg(f"Error: {str(e)}")
