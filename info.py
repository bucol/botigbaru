#!/usr/bin/env python3
"""
Lihat Info Akun Instagram - Bucol Bot
"""

from banner import show_banner, show_separator, success_msg, error_msg
from session_manager import SessionManager
from colorama import Fore, Style

def main():
    show_banner()
    show_separator()
    print(Fore.CYAN + "\n👤 LIHAT INFO AKUN INSTAGRAM" + Style.RESET_ALL)
    show_separator()
    
    username = input(Fore.YELLOW + "\nUsername Instagram: " + Style.RESET_ALL).strip()
    
    session_mgr = SessionManager()
    client = session_mgr.login(username)
    
    if not client:
        error_msg("Login gagal!")
        return
    
    try:
        user_info = client.user_info_by_username(username)
        
        print(Fore.CYAN + "\n╔════════════════════════════════════════════════════════╗")
        print(f"║  {Fore.MAGENTA}📱 INFORMASI AKUN INSTAGRAM{Fore.CYAN}                          ║")
        print("╠════════════════════════════════════════════════════════╣" + Style.RESET_ALL)
        print(Fore.YELLOW + f"  🆔 User ID        : " + Fore.WHITE + f"{user_info.pk}")
        print(Fore.YELLOW + f"  👤 Username       : " + Fore.WHITE + f"@{user_info.username}")
        print(Fore.YELLOW + f"  📝 Full Name      : " + Fore.WHITE + f"{user_info.full_name}")
        print(Fore.YELLOW + f"  📖 Bio            : " + Fore.WHITE + f"{user_info.biography or '(kosong)'}")
        print(Fore.YELLOW + f"  📧 Email          : " + Fore.WHITE + f"{user_info.public_email or '(tidak public)'}")
        print(Fore.YELLOW + f"  👥 Followers      : " + Fore.GREEN + f"{user_info.follower_count:,}")
        print(Fore.YELLOW + f"  👣 Following      : " + Fore.GREEN + f"{user_info.following_count:,}")
        print(Fore.YELLOW + f"  📸 Posts          : " + Fore.GREEN + f"{user_info.media_count:,}")
        print(Fore.YELLOW + f"  🔒 Private        : " + Fore.WHITE + f"{'Ya' if user_info.is_private else 'Tidak'}")
        print(Fore.YELLOW + f"  ✓  Verified       : " + Fore.WHITE + f"{'Ya ✓' if user_info.is_verified else 'Tidak'}")
        print(Fore.CYAN + "╚════════════════════════════════════════════════════════╝" + Style.RESET_ALL)
        
        success_msg("Info akun berhasil ditampilkan!")
        
    except Exception as e:
        error_msg(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
