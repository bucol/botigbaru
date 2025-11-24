#!/usr/bin/env python3
"""
Tampilkan info akun Instagram, dengan detail email (jika ada)
"""

from banner import show_separator, success_msg, error_msg
from colorama import Fore, Style

def view_account_info(client, username):
    show_separator()
    print(Fore.CYAN + "\n👤 LIHAT INFO AKUN INSTAGRAM" + Style.RESET_ALL)
    show_separator()
    try:
        # Akurat dan lebih lengkap ambil dari kedua API
        user_info = client.user_info_by_username(username)
        try:
            account_info = client.account_info()
            email = account_info.get("email", "")
            # Kalau kosong, fallback
            if not email and hasattr(user_info, "public_email"):
                email = user_info.public_email or ""
        except Exception:
            email = getattr(user_info, "public_email", "") or ""

        # Info detail standard user
        print(Fore.CYAN + "\n╔════════════════════════════════════════════════════════╗")
        print(f"║  {Fore.MAGENTA}📱 INFORMASI AKUN INSTAGRAM{Fore.CYAN}                          ║")
        print("╠════════════════════════════════════════════════════════╣" + Style.RESET_ALL)
        print(Fore.YELLOW + f"  🆔 User ID        : " + Fore.WHITE + f"{user_info.pk}")
        print(Fore.YELLOW + f"  👤 Username       : " + Fore.WHITE + f"@{user_info.username}")
        print(Fore.YELLOW + f"  📝 Full Name      : " + Fore.WHITE + f"{user_info.full_name}")
        print(Fore.YELLOW + f"  📖 Bio            : " + Fore.WHITE + f"{user_info.biography or '(kosong)'}")
        print(Fore.YELLOW + f"  📧 Email          : " + Fore.WHITE + f"{email if email else '(tidak tersedia)'}")
        print(Fore.YELLOW + f"  👥 Followers      : " + Fore.GREEN + f"{user_info.follower_count:,}")
        print(Fore.YELLOW + f"  👣 Following      : " + Fore.GREEN + f"{user_info.following_count:,}")
        print(Fore.YELLOW + f"  📸 Posts          : " + Fore.GREEN + f"{user_info.media_count:,}")
        print(Fore.YELLOW + f"  🔒 Private        : " + Fore.WHITE + f"{'Ya' if user_info.is_private else 'Tidak'}")
        print(Fore.YELLOW + f"  ✓  Verified       : " + Fore.WHITE + f"{'Ya ✓' if user_info.is_verified else 'Tidak'}")
        print(Fore.CYAN + "╚════════════════════════════════════════════════════════╝" + Style.RESET_ALL)

        success_msg("Info akun berhasil ditampilkan!\n")

    except Exception as e:
        error_msg(f"Error: {str(e)}")
