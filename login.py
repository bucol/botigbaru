#!/usr/bin/env python3
"""
Login Instagram - Bucol Bot
"""

from banner import show_banner, show_separator, success_msg
from session_manager import SessionManager
from colorama import Fore, Style

def main():
    try:
        show_banner()
        show_separator()
        print(Fore.CYAN + "\n🔐 LOGIN INSTAGRAM" + Style.RESET_ALL)
        show_separator()
        
        username = input(Fore.YELLOW + "\nUsername Instagram: " + Style.RESET_ALL).strip()
        
        session_mgr = SessionManager()
        client = session_mgr.login(username)
        
        if client:
            print(Fore.GREEN + "\n🎉 Berhasil login dan session tersimpan!" + Style.RESET_ALL)
            print(Fore.CYAN + "💾 File session: instagram_settings.json" + Style.RESET_ALL)
        else:
            print(Fore.RED + "\n❌ Login gagal!" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"\nError: {str(e)}" + Style.RESET_ALL)

if __name__ == "__main__":
    main()