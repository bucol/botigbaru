#!/usr/bin/env python3
"""
Block/Unblock Manager
Manage blocked accounts
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import json
import os
import time

class BlockUnblockManager:
    def __init__(self, client):
        self.client = client
        self.blocked_list_file = "data/blocked_accounts.json"
        self.load_blocked_list()

    def load_blocked_list(self):
        """Load blocked accounts list"""
        os.makedirs("data", exist_ok=True)

        if os.path.exists(self.blocked_list_file):
            try:
                with open(self.blocked_list_file, 'r', encoding='utf-8') as f:
                    self.blocked_list = json.load(f)
            except:
                self.blocked_list = []
        else:
            self.blocked_list = []

    def save_blocked_list(self):
        """Save blocked accounts"""
        try:
            with open(self.blocked_list_file, 'w', encoding='utf-8') as f:
                json.dump(self.blocked_list, f, indent=4, ensure_ascii=False)
        except Exception as e:
            warning_msg(f"Error save list: {str(e)}")

    def block_user(self, user_id, username):
        """Block satu user"""
        try:
            self.client.user_block(user_id)

            self.blocked_list.append({
                'user_id': user_id,
                'username': username,
                'blocked_at': __import__('datetime').datetime.now().isoformat()
            })

            self.save_blocked_list()
            success_msg(f"✅ Blocked @{username}")

        except Exception as e:
            error_msg(f"Error block: {str(e)}")

    def unblock_user(self, user_id, username):
        """Unblock satu user"""
        try:
            self.client.user_unblock(user_id)

            self.blocked_list = [b for b in self.blocked_list if b['user_id'] != user_id]

            self.save_blocked_list()
            success_msg(f"✅ Unblocked @{username}")

        except Exception as e:
            error_msg(f"Error unblock: {str(e)}")

    def view_blocked_list(self):
        """View list akun yang di-block"""
        if not self.blocked_list:
            warning_msg("No blocked accounts")
            return

        show_separator()
        print(Fore.CYAN + "\n🚫 BLOCKED ACCOUNTS" + Style.RESET_ALL)
        show_separator()

        for i, blocked in enumerate(self.blocked_list, 1):
            print(f"\n{i}. @{blocked['username']}")
            print(f"   ID: {blocked['user_id']}")
            print(f"   Blocked: {blocked['blocked_at'][:10]}")

    def bulk_block_from_file(self):
        """Bulk block dari file"""
        try:
            filename = input(Fore.YELLOW + "\nMasukkan nama file (usernames, satu per baris): " + Style.RESET_ALL).strip()

            if not os.path.exists(filename):
                error_msg("File not found!")
                return

            with open(filename, 'r', encoding='utf-8') as f:
                usernames = [line.strip() for line in f.readlines() if line.strip()]

            if not usernames:
                warning_msg("No usernames in file")
                return

            info_msg(f"Blocking {len(usernames)} accounts...")

            blocked_count = 0

            for i, username in enumerate(usernames, 1):
                try:
                    user_id = self.client.user_id_from_username(username)
                    self.block_user(user_id, username)
                    blocked_count += 1
                    print(f"  [{i}/{len(usernames)}]")
                    time.sleep(2)

                except Exception as e:
                    warning_msg(f"Error block @{username}: {str(e)}")
                    continue

            success_msg(f"✅ Blocked {blocked_count}/{len(usernames)} accounts")

        except Exception as e:
            error_msg(f"Error: {str(e)}")

    def run_block_manager_menu(self):
        """Menu block manager"""
        show_separator()
        print(Fore.CYAN + "\n🚫 BLOCK/UNBLOCK MANAGER" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nPilih aksi:" + Style.RESET_ALL)
            print("1. 📋 View blocked accounts")
            print("2. 🚫 Block single account")
            print("3. ✅ Unblock account")
            print("4. 📂 Bulk block from file")
            print("0. ❌ Batal")

            choice = input(Fore.MAGENTA + "\nPilih (0-4): " + Style.RESET_ALL).strip()

            if choice == '0':
                return

            elif choice == '1':
                self.view_blocked_list()

            elif choice == '2':
                username = input(Fore.YELLOW + "\nMasukkan username: " + Style.RESET_ALL).strip()

                if username:
                    try:
                        user_id = self.client.user_id_from_username(username)
                        self.block_user(user_id, username)
                    except Exception as e:
                        error_msg(f"Error: {str(e)}")

            elif choice == '3':
                self.view_blocked_list()
                username = input(Fore.YELLOW + "\nMasukkan username untuk unblock: " + Style.RESET_ALL).strip()

                blocked = next((b for b in self.blocked_list if b['username'] == username), None)

                if blocked:
                    self.unblock_user(blocked['user_id'], username)
                else:
                    error_msg("Account not in blocked list")

            elif choice == '4':
                self.bulk_block_from_file()

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def block_unblock_menu(client):
    """Menu wrapper"""
    manager = BlockUnblockManager(client)
    manager.run_block_manager_menu()
