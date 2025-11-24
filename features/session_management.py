#!/usr/bin/env python3
"""
Session Management:
- Backup session file
- Restore session file
- Check session validity
- Handle session invalid
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import os
import shutil
from datetime import datetime

class SessionTools:
    def __init__(self, sessions_dir="sessions"):
        self.sessions_dir = sessions_dir
        self.backup_dir = "session_backups"
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)

    def backup_session(self, username):
        """Backup session file untuk user tertentu"""
        show_separator()
        print(Fore.CYAN + "\n💾 BACKUP SESSION FILE" + Style.RESET_ALL)
        show_separator()

        try:
            session_file = os.path.join(self.sessions_dir, f"{username}_session.json")
            
            if not os.path.exists(session_file):
                error_msg(f"Session @{username} tidak ditemukan!")
                return False

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"{username}_session_backup_{timestamp}.json")
            
            shutil.copy2(session_file, backup_file)
            success_msg(f"Session @{username} berhasil di-backup!")
            info_msg(f"File backup: {backup_file}")
            return True

        except Exception as e:
            error_msg(f"Error saat backup session: {str(e)}")
            return False

    def restore_session(self, username):
        """Restore session dari backup file"""
        show_separator()
        print(Fore.CYAN + "\n♻️  RESTORE SESSION FILE" + Style.RESET_ALL)
        show_separator()

        try:
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith(f"{username}_session_backup")]
            
            if not backup_files:
                warning_msg(f"Tidak ada backup session untuk @{username}")
                return False

            backup_files.sort(reverse=True)
            
            print(Fore.YELLOW + "\nDaftar backup session yang tersedia:" + Style.RESET_ALL)
            for i, backup_file in enumerate(backup_files, 1):
                file_path = os.path.join(self.backup_dir, backup_file)
                file_size = os.path.getsize(file_path)
                file_time = backup_file.split("_")[-2] + "_" + backup_file.split("_")[-1].replace(".json", "")
                print(f"{i}. {backup_file} ({file_size} bytes) - {file_time}")

            choice = input(Fore.YELLOW + f"\nPilih backup (1-{len(backup_files)}): " + Style.RESET_ALL).strip()
            
            try:
                choice_num = int(choice)
                if choice_num < 1 or choice_num > len(backup_files):
                    error_msg("Pilihan tidak valid!")
                    return False
            except ValueError:
                error_msg("Input harus angka!")
                return False

            selected_backup = backup_files[choice_num - 1]
            backup_file_path = os.path.join(self.backup_dir, selected_backup)
            session_file = os.path.join(self.sessions_dir, f"{username}_session.json")

            confirm = input(Fore.MAGENTA + f"\n⚠️  Yakin restore dari backup ini? (yes/no): " + Style.RESET_ALL).strip().lower()
            if confirm != "yes":
                info_msg("Restore dibatalkan!")
                return False

            shutil.copy2(backup_file_path, session_file)
            success_msg(f"Session @{username} berhasil di-restore!")
            return True

        except Exception as e:
            error_msg(f"Error saat restore session: {str(e)}")
            return False

    def list_backups(self, username=None):
        """Daftar semua backup session"""
        show_separator()
        print(Fore.CYAN + "\n📋 DAFTAR BACKUP SESSION" + Style.RESET_ALL)
        show_separator()

        try:
            backup_files = os.listdir(self.backup_dir)
            
            if not backup_files:
                warning_msg("Tidak ada backup session tersimpan!")
                return

            if username:
                backup_files = [f for f in backup_files if f.startswith(f"{username}_session_backup")]

            if not backup_files:
                warning_msg(f"Tidak ada backup session untuk @{username}")
                return

            backup_files.sort(reverse=True)
            
            print(Fore.YELLOW + "\nBackup session yang tersimpan:" + Style.RESET_ALL)
            for i, backup_file in enumerate(backup_files, 1):
                file_path = os.path.join(self.backup_dir, backup_file)
                file_size = os.path.getsize(file_path)
                print(f"{i}. {backup_file} ({file_size} bytes)")

        except Exception as e:
            error_msg(f"Error saat list backup: {str(e)}")

    def delete_backup(self, username):
        """Hapus backup session tertentu"""
        show_separator()
        print(Fore.RED + "\n🗑️  HAPUS BACKUP SESSION" + Style.RESET_ALL)
        show_separator()

        try:
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith(f"{username}_session_backup")]
            
            if not backup_files:
                warning_msg(f"Tidak ada backup session untuk @{username}")
                return False

            backup_files.sort(reverse=True)
            
            print(Fore.YELLOW + "\nPilih backup yang mau dihapus:" + Style.RESET_ALL)
            for i, backup_file in enumerate(backup_files, 1):
                print(f"{i}. {backup_file}")

            choice = input(Fore.YELLOW + f"\nPilih backup (1-{len(backup_files)}): " + Style.RESET_ALL).strip()
            
            try:
                choice_num = int(choice)
                if choice_num < 1 or choice_num > len(backup_files):
                    error_msg("Pilihan tidak valid!")
                    return False
            except ValueError:
                error_msg("Input harus angka!")
                return False

            selected_backup = backup_files[choice_num - 1]
            backup_file_path = os.path.join(self.backup_dir, selected_backup)

            confirm = input(Fore.RED + f"\n⚠️  Yakin hapus backup ini? (yes/no): " + Style.RESET_ALL).strip().lower()
            if confirm != "yes":
                info_msg("Penghapusan dibatalkan!")
                return False

            os.remove(backup_file_path)
            success_msg(f"Backup berhasil dihapus!")
            return True

        except Exception as e:
            error_msg(f"Error saat hapus backup: {str(e)}")
            return False

def session_management_menu(username):
    """Menu management session untuk user tertentu"""
    tools = SessionTools()

    while True:
        show_separator()
        print(Fore.CYAN + f"\n💾 SESSION MANAGEMENT - @{username}" + Style.RESET_ALL)
        show_separator()
        print(Fore.YELLOW + "\n1. 💾 Backup Session")
        print("2. ♻️  Restore Session")
        print("3. 📋 Daftar Backup")
        print("4. 🗑️  Hapus Backup")
        print("0. ❌ Kembali" + Style.RESET_ALL)
        show_separator()

        choice = input(Fore.MAGENTA + "\nPilih menu (0-4): " + Style.RESET_ALL).strip()

        if choice == '1':
            tools.backup_session(username)
        elif choice == '2':
            tools.restore_session(username)
        elif choice == '3':
            tools.list_backups(username)
        elif choice == '4':
            tools.delete_backup(username)
        elif choice == '0':
            info_msg("Kembali ke menu utama...")
            break
        else:
            error_msg("Pilihan tidak valid!")

        input(Fore.CYAN + "\nTekan Enter untuk lanjut..." + Style.RESET_ALL)
