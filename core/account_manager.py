#!/usr/bin/env python3
"""
Account Manager - Production Fixed Version
Tugas: Menyimpan username/password terenkripsi dan menyediakannya untuk LoginManager.
Fitur Baru: Auto-fix jika format JSON rusak/salah tipe data.
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
        """
        Load accounts dengan Safety Check.
        Jika formatnya List (salah), akan di-reset jadi Dictionary (benar).
        """
        try:
            if not os.path.exists(self.accounts_file):
                return {}
                
            with open(self.accounts_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                    
                data = json.loads(content)
                
                # --- FIX: Cek tipe data ---
                if isinstance(data, list):
                    logger.warning("⚠️ Format accounts.json salah (List). Mereset menjadi Dictionary.")
                    return {} # Reset ke dict kosong agar tidak error
                
                return data
                
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"⚠️ Error loading accounts: {e}. Resetting DB.")
            return {}

    def _save_accounts(self, data: dict):
        # Pastikan yang disimpan selalu DICTIONARY
        if not isinstance(data, dict):
            data = {} 
            
        with open(self.accounts_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_accounts(self) -> list:
        """
        Public API: Mengembalikan list semua akun dengan password yang SUDAH DIDEKRIPSI.
        """
        data = self._load_accounts()
        account_list = []
        
        # Safety check extra
        if not isinstance(data, dict):
            return []

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
        # Tidak perlu print disini karena setup_wizard sudah ada print success

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
        
        if not data:
            print("   (Kosong)")
            return

        for user, info in data.items():
            status = "🟢" if info.get('is_active', True) else "🔴"
            print(f" {status} {user} | Note: {info.get('note', '-')}")
        print("")

if __name__ == "__main__":
    mgr = AccountManager()
    print("Account Manager Fixed Loaded.")