#!/usr/bin/env python3
"""
Multi-Account Switcher
Switch antar akun tanpa re-login
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import json
import os

class AccountSwitcher:
    def __init__(self, session_mgr):
        self.session_mgr = session_mgr
        self.favorites_file = "data/favorite_accounts.json"
        self.load_favorites()

    def load_favorites(self):
        """Load favorite accounts"""
        os.makedirs("data", exist_ok=True)

        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    self.favorites = json.load(f)
            except:
                self.favorites = []
        else:
            self.favorites = []

    def save_favorites(self):
        """Save favorite accounts"""
        try:
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, indent=4, ensure_ascii=False)
        except Exception as e:
            warning_msg(f"Error save favorites: {str(e)}")

    def add_favorite(self, username):
        """Add akun ke favorites"""
        if username not in self.favorites:
            self.favorites.append(username)
            self.save_favorites()
            success_msg(f"✅ @{username} added to favorites")
        else:
            warning_msg("Already in favorites")

    def remove_favorite(self, username):
        """Remove dari favorites"""
        if username in self.favorites:
            self.favorites.remove(username)
            self.save_favorites()
            success_msg(f"✅ @{username} removed from favorites")
        else:
            warning_msg("Not in favorites")

    def display_favorites(self):
        """Display favorite accounts"""
        if not self.favorites:
            warning_msg("No favorite accounts")
            return

        print(Fore.YELLOW + "\n⭐ FAVORITE ACCOUNTS:" + Style.RESET_ALL)
        for i, account in enumerate(self.favorites, 1):
            print(f"  {i}. @{account}")

    def display_all_accounts(self):
        """Display all saved accounts"""
        accounts = self.session_mgr.get_all_saved_accounts()

        if not accounts:
            warning_msg("No saved accounts")
            return

        print(Fore.YELLOW + "\n📱 ALL SAVED ACCOUNTS:" + Style.RESET_ALL)

        for i, account in enumerate(accounts, 1):
            is_favorite = "⭐" if account in self.favorites else "  "
            print(f"  {is_favorite} {i}. @{account}")

    def switch_account(self, username):
        """Switch ke akun tertentu"""
        try:
            info_msg(f"Switching to @{username}...")
            client = self.session_mgr.login(username)

            if client:
                success_msg(f"✅ Switched to @{username}")
                return client
            else:
                error_msg("Switch failed!")
                return None

        except Exception as e:
            error_msg(f"Error: {str(e)}")
            return None

    def run_switcher_menu(self):
        """Menu account switcher"""
        show_separator()
        print(Fore.CYAN + "\n🔄 MULTI-ACCOUNT SWITCHER" + Style.RESET_ALL)
        show_separator()

        try:
            accounts = self.session_mgr.get_all_saved_accounts()

            print(Fore.YELLOW + "\nPilih aksi:" + Style.RESET_ALL)
            print("1. 📋 View all accounts")
            print("2. ⭐ View favorite accounts")
            print("3. 🔄 Quick switch (favorites)")
            print("4. ⭐ Add to favorites")
            print("5. 🗑️  Remove from favorites")
            print("0. ❌ Batal")

            choice = input(Fore.MAGENTA + "\nPilih (0-5): " + Style.RESET_ALL).strip()

            if choice == '0':
                return None

            elif choice == '1':
                self.display_all_accounts()

            elif choice == '2':
                self.display_favorites()

            elif choice == '3':
                self.display_favorites()

                if self.favorites:
                    fav_choice = input(Fore.MAGENTA + "\nPilih akun (nomor): " + Style.RESET_ALL).strip()

                    try:
                        fav_idx = int(fav_choice) - 1

                        if 0 <= fav_idx < len(self.favorites):
                            selected = self.favorites[fav_idx]
                            return self.switch_account(selected)
                        else:
                            error_msg("Invalid choice")
                            return None
                    except ValueError:
                        error_msg("Input must be number")
                        return None

            elif choice == '4':
                self.display_all_accounts()

                username = input(Fore.MAGENTA + "\nUsername to add: " + Style.RESET_ALL).strip()

                if username in accounts:
                    self.add_favorite(username)
                else:
                    error_msg("Account not found")

            elif choice == '5':
                self.display_favorites()

                if self.favorites:
                    username = input(Fore.MAGENTA + "\nUsername to remove: " + Style.RESET_ALL).strip()

                    if username in self.favorites:
                        self.remove_favorite(username)
                    else:
                        error_msg("Not in favorites")

            return None

        except Exception as e:
            error_msg(f"Error: {str(e)}")
            return None

def account_switcher_menu(session_mgr):
    """Menu wrapper"""
    switcher = AccountSwitcher(session_mgr)
    return switcher.run_switcher_menu()
