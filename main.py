import warnings
import logging
import os
import sys

warnings.filterwarnings("ignore")
logging.getLogger("instagrapi").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

class DummyFile(object):
    def write(self, x): pass
    def flush(self): pass

import builtins
def silent_print(*args, **kwargs):
    if args and isinstance(args[0], str) and 'JSONDecodeError in public_request' in args[0]:
        return
    return original_print(*args, **kwargs)

original_print = builtins.print
builtins.print = silent_print

from banner import show_banner, show_separator, error_msg, success_msg, info_msg, warning_msg
from session_manager import SessionManager
from colorama import Fore, Style
import getpass

# EXISTING FEATURES
from features.view_info import view_account_info
from features.upload_profile_pic import upload_profile_picture
from features.edit_name import edit_full_name
from features.edit_username import edit_username
from features.edit_bio import edit_bio
from features.post_photo import post_photo
from features.post_reel import post_reel
from features.session_management import session_management_menu
from features.auto_setup_accounts import auto_setup_accounts_menu
from features.md5_hash_changer import md5_hash_changer_menu
from features.auto_like_comment import auto_like_comment
from features.auto_follow_unfollow import auto_follow_unfollow
from features.auto_dm import auto_dm
from features.scheduled_posting import scheduled_posting_menu

# PHASE 1 FEATURES (Safe Import)
try:
    from features.discovery_growth.hashtag_research import hashtag_research_menu
    from features.discovery_growth.competitor_analysis import competitor_analysis_menu
    from features.content_management.content_backup import content_backup_menu
    from features.analytics.engagement_analytics_enhanced import engagement_analytics_menu
    PHASE1_AVAILABLE = True
except ImportError:
    PHASE1_AVAILABLE = False

# PHASE 2 FEATURES (Safe Import)
try:
    from features.creative.caption_generator import caption_generator_menu
    from features.content_management.bulk_delete_posts import bulk_delete_menu
    from features.automation.smart_unfollow import smart_unfollow_menu
    from features.security_privacy.privacy_settings import privacy_settings_menu
    from features.automation.anti_detection import anti_detection_menu
    PHASE2_AVAILABLE = True
except ImportError:
    PHASE2_AVAILABLE = False

# PHASE 3 FEATURES (Safe Import)
try:
    from features.creative.story_template import story_template_menu
    from features.notifications.notification_system import notification_system_menu
    from features.security_privacy.block_unblock_manager import block_unblock_menu
    from features.multi_account.account_switcher import account_switcher_menu
    from features.security_privacy.login_monitor import login_monitor_menu
    from features.security_privacy.account_type_converter import account_type_converter_menu
    PHASE3_AVAILABLE = True
except ImportError:
    PHASE3_AVAILABLE = False

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def select_account_menu():
    clear_screen()
    show_banner()
    
    session_mgr = SessionManager()
    saved_accounts = session_mgr.get_all_saved_accounts()

    show_separator()
    print(Fore.CYAN + "\n🔐 PILIH AKUN INSTAGRAM" + Style.RESET_ALL)
    show_separator()

    print(Fore.MAGENTA + "\n🔝 MENU UTAMA:" + Style.RESET_ALL)
    print(Fore.MAGENTA + "  1. 🤖 Auto Setup Semua Akun" + Style.RESET_ALL)
    print(Fore.MAGENTA + "  2. 🔐 MD5 Hash Changer" + Style.RESET_ALL)
    print(Fore.MAGENTA + "  3. 📱 List Akun & Pilih Akun" + Style.RESET_ALL)
    print(Fore.CYAN + "  0. ❌ Keluar" + Style.RESET_ALL)
    show_separator()

    choice = input(Fore.MAGENTA + "\nPilih menu (0-3): " + Style.RESET_ALL).strip()

    try:
        choice_num = int(choice)
        
        if choice_num == 0:
            print(Fore.GREEN + "\n👋 Terima kasih! Sampai jumpa!" + Style.RESET_ALL)
            sys.exit(0)
        elif choice_num == 1:
            auto_setup_accounts_menu()
            return None, None
        elif choice_num == 2:
            md5_hash_changer_menu()
            return None, None
        elif choice_num == 3:
            return select_saved_account_menu(session_mgr, saved_accounts)
        else:
            error_msg("Pilihan tidak valid!")
            return None, None

    except ValueError:
        error_msg("Input harus angka!")
        return None, None

def select_saved_account_menu(session_mgr, saved_accounts):
    """Menu untuk pilih akun"""
    clear_screen()
    show_separator()
    print(Fore.CYAN + "\n📱 DAFTAR AKUN & OPSI" + Style.RESET_ALL)
    show_separator()

    print(Fore.YELLOW + "\n📋 AKUN YANG TERSIMPAN:" + Style.RESET_ALL)
    if saved_accounts:
        for i, username in enumerate(saved_accounts, 1):
            print(Fore.YELLOW + f"  {i}. @{username}" + Style.RESET_ALL)
    else:
        print(Fore.RED + "  (Belum ada akun tersimpan)" + Style.RESET_ALL)

    print(Fore.MAGENTA + "\n⚙️  OPSI:" + Style.RESET_ALL)
    print(Fore.MAGENTA + f"  {len(saved_accounts) + 1}. ➕ Tambah Akun Baru" + Style.RESET_ALL)
    print(Fore.RED + f"  {len(saved_accounts) + 2}. 🗑️  Hapus Session Akun" + Style.RESET_ALL)
    print(Fore.CYAN + "  0. ❌ Kembali" + Style.RESET_ALL)
    show_separator()

    max_choice = len(saved_accounts) + 2
    choice = input(Fore.MAGENTA + f"\nPilih akun atau opsi (0-{max_choice}): " + Style.RESET_ALL).strip()

    try:
        choice_num = int(choice)
        
        if choice_num == 0:
            return None, None
        elif 1 <= choice_num <= len(saved_accounts):
            username = saved_accounts[choice_num - 1]
            info_msg(f"Login dengan akun @{username}...")
            client = session_mgr.login(username)
            if client:
                return client, username
            else:
                error_msg("Login gagal! Session mungkin sudah expired.")
                input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)
                return None, None
        elif choice_num == len(saved_accounts) + 1:
            return login_new_account(session_mgr)
        elif choice_num == len(saved_accounts) + 2:
            return delete_account_session(session_mgr)
        else:
            error_msg("Pilihan tidak valid!")
            return None, None

    except ValueError:
        error_msg("Input harus angka!")
        return None, None

def login_new_account(session_mgr):
    """Login dengan akun baru"""
    clear_screen()
    show_separator()
    print(Fore.CYAN + "\n➕ TAMBAH AKUN BARU" + Style.RESET_ALL)
    show_separator()
    
    try:
        username = input(Fore.YELLOW + "\nUsername Instagram: " + Style.RESET_ALL).strip()
        if not username:
            error_msg("Username tidak boleh kosong!")
            input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)
            return None, None
        
        password = getpass.getpass(Fore.YELLOW + "Password: " + Style.RESET_ALL)
        if not password:
            error_msg("Password tidak boleh kosong!")
            input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)
            return None, None
        
        info_msg(f"🔄 Melakukan login ke @{username}...")
        print(Fore.YELLOW + "(Proses ini mungkin memakan waktu beberapa saat...)" + Style.RESET_ALL)
        
        client = session_mgr.login(username, password)
        
        if client:
            success_msg(f"✅ Login berhasil! Akun @{username} berhasil ditambahkan!")
            print(Fore.GREEN + "\n✓ Session telah disimpan untuk login cepat di masa depan" + Style.RESET_ALL)
            input(Fore.CYAN + "\nTekan Enter untuk lanjut..." + Style.RESET_ALL)
            return client, username
        else:
            error_msg("❌ Login gagal!")
            print(Fore.YELLOW + "\n📝 Kemungkinan penyebab:" + Style.RESET_ALL)
            print("  • Username atau password salah")
            print("  • Akun terkunci atau dibatasi Instagram")
            print("  • Koneksi internet terputus")
            print("  • Perlu verifikasi 2FA/email")
            input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)
            return None, None
    
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n\n⚠️  Login dibatalkan" + Style.RESET_ALL)
        return None, None
    except Exception as e:
        error_msg(f"Error: {str(e)}")
        input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)
        return None, None

def delete_account_session(session_mgr):
    """Hapus session akun"""
    clear_screen()
    saved_accounts = session_mgr.get_all_saved_accounts()
    show_separator()
    print(Fore.RED + "\n🗑️  HAPUS SESSION AKUN" + Style.RESET_ALL)
    show_separator()
    print(Fore.YELLOW + "\nPilih akun yang mau dihapus session-nya:" + Style.RESET_ALL)
    for i, username in enumerate(saved_accounts, 1):
        print(Fore.YELLOW + f"  {i}. @{username}" + Style.RESET_ALL)
    print(Fore.CYAN + "  0. Batal" + Style.RESET_ALL)
    show_separator()
    choice = input(Fore.MAGENTA + f"\nPilih akun (0-{len(saved_accounts)}): " + Style.RESET_ALL).strip()
    try:
        choice_num = int(choice)
        if choice_num == 0:
            info_msg("Dibatalkan!")
            return None, None
        elif 1 <= choice_num <= len(saved_accounts):
            username = saved_accounts[choice_num - 1]
            confirm = input(Fore.RED + f"\n⚠️  Yakin hapus session @{username}? (yes/no): " + Style.RESET_ALL).strip().lower()
            if confirm == "yes":
                session_mgr.delete_session(username)
                success_msg(f"✅ Session @{username} berhasil dihapus!")
                info_msg("Silakan pilih akun lagi atau tambah akun baru.")
                input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)
                return None, None
            else:
                info_msg("Dibatalkan!")
                return None, None
        else:
            error_msg("Pilihan tidak valid!")
            return None, None
    except ValueError:
        error_msg("Input harus angka!")
        return None, None

def check_session_validity(client, username, session_mgr):
    """Cek validity session"""
    try:
        info_msg("Melakukan pengecekan session...")
        if session_mgr.is_session_valid(username):
            success_msg("✅ Session valid dan siap digunakan!")
            return True
        else:
            warning_msg("⚠️  Session tidak valid atau telah expired!")
            print(Fore.YELLOW + "\n📝 INSTRUKSI:" + Style.RESET_ALL)
            print("   1. Session telah invalid atau expired")
            print("   2. Silakan logout dan login kembali")
            return False
    except Exception as e:
        warning_msg(f"Error saat cek session: {str(e)}")
        return False

def main():
    show_banner()
    while True:
        client, username = select_account_menu()
        if client and username:
            break
        else:
            continue

    session_mgr = SessionManager()

    while True:
        clear_screen()
        show_separator()
        print(Fore.CYAN + f"\n📋 MENU UTAMA - BUCOL BOT v3.1" + Style.RESET_ALL)
        print(Fore.GREEN + f"👤 Akun aktif: @{username}" + Style.RESET_ALL)
        show_separator()
        
        print(Fore.YELLOW + "\n👤 ACCOUNT MANAGEMENT:" + Style.RESET_ALL)
        print("  1.  👤 Lihat Info Akun")
        print("  2.  📷 Upload Foto Profil")
        print("  3.  ✏️  Ganti Nama Lengkap")
        print("  4.  🔤 Ganti Username")
        print("  5.  📝 Ganti Bio")
        print("  20. 🔐 Privacy Settings")
        print("  30. 🔄 Account Type Converter (Personal/Creator/Business)")
        
        print("\n📸 POSTING & CONTENT:" + Style.RESET_ALL)
        print("  6.  📸 Post Foto")
        print("  7.  🎥 Post Reels")
        print("  8.  ⏰ Scheduled Posting")
        print("  23. 🗑️  Bulk Delete Posts")
        print("  25. 📸 Story Template Maker")
        
        print("\n✍️  CREATIVE TOOLS:" + Style.RESET_ALL)
        print("  21. ✍️  Caption Generator")
        
        print("\n🤖 AUTOMATION:" + Style.RESET_ALL)
        print("  9.  ❤️  Auto Like & Comment")
        print("  10. 👥 Auto Follow/Unfollow")
        print("  11. 💬 Auto DM")
        print("  22. 🗑️  Smart Unfollow (Advanced)")
        
        print("\n📊 ANALYTICS & INSIGHTS:" + Style.RESET_ALL)
        if PHASE1_AVAILABLE:
            print("  12. 📊 Engagement Analytics (Enhanced)")
            print("  13. 🏷️  Hashtag Research Tool")
            print("  14. 🔍 Competitor Analysis")
            print("  15. 📥 Content Backup")
        else:
            print("  [Phase 1 Features - Not available yet]")
        
        print("\n🔐 SECURITY & MONITORING:" + Style.RESET_ALL)
        print("  24. 🕵️  Anti-Detection System")
        print("  27. 🚫 Block/Unblock Manager")
        print("  28. 🔐 Login Activity Monitor")
        
        print("\n🔔 NOTIFICATIONS:" + Style.RESET_ALL)
        print("  26. 🔔 Notification System (Real-time Alerts)")
        
        print("\n🔄 MULTI-ACCOUNT MANAGEMENT:" + Style.RESET_ALL)
        print("  29. 🔄 Multi-Account Switcher (Quick Switch)")
        
        print("\n⚙️  SESSION & SETTINGS:" + Style.RESET_ALL)
        print("  16. 💾 Session Management")
        print("  17. ✅ Cek Session Validity")
        print("  18. 🔄 Ganti Akun")
        print("  19. 🚪 Logout & Hapus Session")
        
        print("\n" + Fore.CYAN + "  0.  ❌ Keluar" + Style.RESET_ALL)
        
        show_separator()
        choice = input(Fore.MAGENTA + "\nPilih menu (0-30): " + Style.RESET_ALL).strip()

        try:
            if choice == '0':
                print(Fore.GREEN + "\n👋 Terima kasih! Sampai jumpa!" + Style.RESET_ALL)
                sys.exit(0)
            elif choice == '1':
                clear_screen()
                view_account_info(client, username)
            elif choice == '2':
                clear_screen()
                upload_profile_picture(client)
            elif choice == '3':
                clear_screen()
                edit_full_name(client)
            elif choice == '4':
                clear_screen()
                username = edit_username(client, username)
            elif choice == '5':
                clear_screen()
                edit_bio(client, username)
            elif choice == '6':
                clear_screen()
                post_photo(client)
            elif choice == '7':
                clear_screen()
                post_reel(client)
            elif choice == '8':
                clear_screen()
                scheduled_posting_menu(client, username)
            elif choice == '9':
                clear_screen()
                auto_like_comment(client, username)
            elif choice == '10':
                clear_screen()
                auto_follow_unfollow(client, username)
            elif choice == '11':
                clear_screen()
                auto_dm(client, username)
            elif choice == '12' and PHASE1_AVAILABLE:
                clear_screen()
                engagement_analytics_menu(client, username)
            elif choice == '13' and PHASE1_AVAILABLE:
                clear_screen()
                hashtag_research_menu(client)
            elif choice == '14' and PHASE1_AVAILABLE:
                clear_screen()
                competitor_analysis_menu(client, username)
            elif choice == '15' and PHASE1_AVAILABLE:
                clear_screen()
                content_backup_menu(client, username)
            elif choice == '16':
                clear_screen()
                session_management_menu(username)
            elif choice == '17':
                clear_screen()
                check_session_validity(client, username, session_mgr)
            elif choice == '18':
                success_msg("Kembali ke menu pemilihan akun...")
                break
            elif choice == '19':
                session_mgr.delete_session(username)
                success_msg("Logout! Session telah dihapus.")
                break
            elif choice == '20' and PHASE2_AVAILABLE:
                clear_screen()
                privacy_settings_menu(client, username)
            elif choice == '21' and PHASE2_AVAILABLE:
                clear_screen()
                caption_generator_menu()
            elif choice == '22' and PHASE2_AVAILABLE:
                clear_screen()
                smart_unfollow_menu(client, username)
            elif choice == '23' and PHASE2_AVAILABLE:
                clear_screen()
                bulk_delete_menu(client, username)
            elif choice == '24' and PHASE2_AVAILABLE:
                clear_screen()
                anti_detection_menu()
            elif choice == '25' and PHASE3_AVAILABLE:
                clear_screen()
                story_template_menu()
            elif choice == '26' and PHASE3_AVAILABLE:
                clear_screen()
                notification_system_menu(client, username)
            elif choice == '27' and PHASE3_AVAILABLE:
                clear_screen()
                block_unblock_menu(client)
            elif choice == '28' and PHASE3_AVAILABLE:
                clear_screen()
                login_monitor_menu(username)
            elif choice == '29' and PHASE3_AVAILABLE:
                clear_screen()
                new_client = account_switcher_menu(session_mgr)
                if new_client:
                    client = new_client
            elif choice == '30' and PHASE3_AVAILABLE:
                clear_screen()
                account_type_converter_menu(client, username)
            else:
                clear_screen()
                warning_msg("Fitur tidak tersedia atau pilihan tidak valid!")
                continue

        except Exception as e:
            clear_screen()
            error_msg(f"Error: {str(e)}")
            continue

        if choice not in ['0', '18', '19']:
            input(Fore.CYAN + "\nTekan Enter untuk lanjut..." + Style.RESET_ALL)

if __name__ == "__main__":
    try:
        while True:
            main()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\n⚠️  Program dihentikan!" + Style.RESET_ALL)
    except Exception as e:
        error_msg(f"Error: {str(e)}")
