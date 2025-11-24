#!/usr/bin/env python3
"""
Privacy Settings Manager
Atur semua pengaturan privacy akun
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style

class PrivacySettings:
    def __init__(self, client):
        self.client = client

    def get_current_settings(self, username):
        """Get current privacy settings"""
        try:
            info_msg("Fetching current settings...")
            user_info = self.client.user_info_by_username(username)

            settings = {
                'is_private': user_info.is_private,
                'username': username
            }

            return settings

        except Exception as e:
            error_msg(f"Error get settings: {str(e)}")
            return None

    def display_settings(self, settings):
        """Display current settings"""
        if not settings:
            return

        show_separator()
        print(Fore.CYAN + "\n🔐 CURRENT PRIVACY SETTINGS" + Style.RESET_ALL)
        show_separator()

        privacy_status = "🔒 PRIVATE" if settings['is_private'] else "🌐 PUBLIC"
        print(f"Account Type: {privacy_status}")

    def change_privacy(self, is_private):
        """Change privacy setting"""
        try:
            self.client.account_edit(is_private=is_private)
            privacy_text = "PRIVATE" if is_private else "PUBLIC"
            success_msg(f"✅ Account set to {privacy_text}")
            return True

        except Exception as e:
            error_msg(f"Error change privacy: {str(e)}")
            return False

    def run_privacy_menu(self, username):
        """Menu privacy settings"""
        show_separator()
        print(Fore.CYAN + "\n🔐 PRIVACY SETTINGS MANAGER" + Style.RESET_ALL)
        show_separator()

        try:
            # Get current
            settings = self.get_current_settings(username)
            if settings:
                self.display_settings(settings)

            print(Fore.YELLOW + "\nPilih aksi:" + Style.RESET_ALL)
            print("1. 🔒 Set to PRIVATE")
            print("2. 🌐 Set to PUBLIC")
            print("0. ❌ Batal")

            choice = input(Fore.MAGENTA + "\nPilih (0-2): " + Style.RESET_ALL).strip()

            if choice == '0':
                info_msg("Dibatalkan")
                return

            elif choice == '1':
                confirm = input(Fore.MAGENTA + "\nSet account to PRIVATE? (yes/no): " + Style.RESET_ALL).strip().lower()
                if confirm == "yes":
                    self.change_privacy(True)

            elif choice == '2':
                confirm = input(Fore.MAGENTA + "\nSet account to PUBLIC? (yes/no): " + Style.RESET_ALL).strip().lower()
                if confirm == "yes":
                    self.change_privacy(False)

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def privacy_settings_menu(client, username):
    """Menu wrapper"""
    privacy = PrivacySettings(client)
    privacy.run_privacy_menu(username)
