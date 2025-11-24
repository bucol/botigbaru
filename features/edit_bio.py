#!/usr/bin/env python3
"""
Modul: Ganti Bio Instagram
"""

from banner import success_msg, error_msg, info_msg, show_separator
from colorama import Fore, Style

def edit_bio(client, username):
    """Ganti bio Instagram"""
    show_separator()
    print(Fore.CYAN + "\n📝 GANTI BIO" + Style.RESET_ALL)
    show_separator()
    
    try:
        user_info = client.user_info_by_username(username)
        print(Fore.CYAN + f"\nBio sekarang: " + Fore.WHITE + f"{user_info.biography or '(kosong)'}" + Style.RESET_ALL)
        
        print(Fore.YELLOW + "\nMasukkan bio baru (tekan Enter 2x untuk selesai):" + Style.RESET_ALL)
        lines = []
        while True:
            line = input()
            if line == "" and len(lines) > 0:
                break
            lines.append(line)
        
        new_bio = "\n".join(lines)
        
        info_msg("Mengubah bio...")
        client.account_edit(biography=new_bio)
        success_msg("Bio berhasil diubah! 🎉")
        
    except Exception as e:
        error_msg(f"Error: {str(e)}")
