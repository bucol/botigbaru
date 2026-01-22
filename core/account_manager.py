#!/usr/bin/env python3
"""
Account Manager - Integrated Version
Tugas: Menyimpan username/password terenkripsi dan menyediakannya untuk LoginManager.
"""

import os
import json
import datetime
import logging
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AccountManager:
    def __init__(self, accounts_file="data/accounts.json", key_file=".secret.key"):
        # Saya pindahkan ke folder data/ agar lebih rapi sesuai struktur folder kamu
        self.accounts_file = accounts_file 
        self.key_file = key_file
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.accounts_file), exist_ok=True)
        
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)

        # Create empty db if not exists
        if not os.path.exists(self.accounts_file):
            self._save_accounts({})

    # ====================================================
    # 🔐 ENCRYPTION
    # ====================================================
    def _load_or_generate_key(self) -> bytes:
        if os.path.exists(self.key_file):
            with open(self.key_file, "rb") as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as f:
                f.write(key)
            print("🗝️  New encryption key generated.")
            return key

    def encrypt(self, text: str) -> str:
        return self.fernet.encrypt(text.encode()).decode()

    def decrypt(self, token: str) -> str:
        try:
            return self.fernet.decrypt(token.encode()).decode()
        except Exception:
            return "[decryption_failed]"

    # ====================================================
    # 🧠 DATA ACCESS (CRUD)
    # ====================================================
    def _load_accounts(self) -> dict:
        try:
            with open(self.accounts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_accounts(self, data: dict):
        with open(self.accounts_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_accounts(self) -> list:
        """
        Public API: Mengembalikan list semua akun dengan password yang SUDAH DIDEKRIPSI.
        Digunakan oleh LoginManager untuk proses login.
        """
        data = self._load_accounts()
        account_list = []
        for username, info in data.items():
            try:
                decrypted_pass = self.decrypt(info['password'])
                account_list.append({
                    'username': username,
                    'password': decrypted_pass,
                    'note': info.get('note', ''),
                    'is_active': info.get('is_active', True)
                })
            except Exception:
                logger.error(f"Failed to decrypt password for {username}")
        return account_list

    def add_account(self, username: str, password: str, note: str = ""):
        data = self._load_accounts()
        if username in data:
            print(f"⚠️ Akun '{username}' sudah ada. Update password...")
        
        data[username] = {
            "password": self.encrypt(password),
            "note": note,
            "added_at": datetime.datetime.utcnow().isoformat(),
            "is_active": True
        }
        self._save_accounts(data)
        print(f"✅ Akun '{username}' berhasil disimpan (Terenkripsi).")

    def remove_account(self, username: str):
        data = self._load_accounts()
        if username in data:
            del data[username]
            self._save_accounts(data)
            print(f"🗑️ Akun '{username}' dihapus.")
        else:
            print(f"⚠️ Akun '{username}' tidak ditemukan.")

    def list_accounts_safe(self):
        """Menampilkan daftar akun tanpa password"""
        data = self._load_accounts()
        print("\n📂 Daftar Akun Tersimpan:")
        for user, info in data.items():
            status = "🟢" if info.get('is_active', True) else "🔴"
            print(f" {status} {user} | Note: {info.get('note', '-')}")
        print("")

if __name__ == "__main__":
    # CLI Sederhana untuk Manajemen Akun
    mgr = AccountManager()
    print("=== Account Database Manager ===")
    while True:
        c = input("1. Add/Update Account\n2. List Accounts\n3. Delete Account\n4. Exit\nPilih: ")
        if c == '1':
            u = input("Username: ")
            p = input("Password: ")
            n = input("Note: ")
            mgr.add_account(u, p, n)
        elif c == '2':
            mgr.list_accounts_safe()
        elif c == '3':
            u = input("Username: ")
            mgr.remove_account(u)
        elif c == '4':
            break