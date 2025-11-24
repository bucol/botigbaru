#!/usr/bin/env python3
"""
Ganti Username Instagram - Bucol Bot
Auto-rename session file setelah sukses ganti username
"""

from banner import show_banner, show_separator, success_msg, error_msg, info_msg, warning_msg
from session_manager import SessionManager
from colorama import Fore, Style
import os

def auto_rename_session_file(old_username, new_username):
    old_file = os.path.join("sessions", f"{old_username}_session.json")
    new_file = os.path.join("sessions", f"{new_username}_session.json")
    if os.path.exists(old_file):
        os.rename(old_file, new_file)
        info_msg(f"Session file sudah dipindahkan: {new_file}")

def edit_username(client, current_username):
    """Ganti username Instagram dan auto rename session file"""
    show_separator()
    print(Fore.CYAN + "\n🔤 GANTI USERNAME" + Style.RESET_ALL)
    show_separator()

    try:
        warning_msg("WARNING: Ganti username adalah perubahan PERMANEN!")
        warning_msg("Username lama akan tersedia untuk diambil orang lain!")
        print(Fore.CYAN + f"\nUsername sekarang: " + Fore.WHITE + f"@{current_username}" + Style.RESET_ALL)
        new_username = input(Fore.YELLOW + "Username baru: " + Style.RESET_ALL).strip()
        if not new_username:
            error_msg("Username tidak boleh kosong!")
            return current_username
        
        confirm = input(Fore.MAGENTA + f"\n⚠️  Yakin ganti ke @{new_username}? (yes/no): " + Style.RESET_ALL).strip().lower()
        if confirm != "yes":
            info_msg("Dibatalkan!")
            return current_username

        info_msg("Mengubah username...")
        client.account_edit(username=new_username)
        success_msg(f"Username berhasil diubah menjadi: @{new_username} 🎉")

        # === Auto-rename session file ===
        auto_rename_session_file(current_username, new_username)
        success_msg(f"Session sekarang menggunakan nama: {new_username}_session.json")
        warning_msg("Mulai sekarang login dengan username baru!")

        return new_username

    except Exception as e:
        error_msg(f"Error: {str(e)}")
        warning_msg("Kemungkinan username sudah dipakai/invalid")
        return current_username
