#!/usr/bin/env python3
"""
Modul: Ganti Nama Lengkap Instagram
"""

from banner import success_msg, error_msg, info_msg, show_separator
from colorama import Fore, Style

def edit_full_name(client):
    """Ganti nama lengkap Instagram"""
    show_separator()
    print(Fore.CYAN + "\n✏️  GANTI NAMA LENGKAP" + Style.RESET_ALL)
    show_separator()
    
    try:
        user_info = client.account_info()
        print(Fore.CYAN + f"\nNama sekarang: " + Fore.WHITE + f"{user_info['full_name']}" + Style.RESET_ALL)
        
        new_name = input(Fore.YELLOW + "Nama baru: " + Style.RESET_ALL).strip()
        
        if not new_name:
            error_msg("Nama tidak boleh kosong!")
            return
        
        info_msg("Mengubah nama...")
        client.account_edit(full_name=new_name)
        success_msg(f"Nama berhasil diubah menjadi: {new_name} 🎉")
        
    except Exception as e:
        error_msg(f"Error: {str(e)}")
