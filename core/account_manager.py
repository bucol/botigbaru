#!/usr/bin/env python3
"""
Account Manager - Production Fixed Version

Tugas:
- Simpan & kelola akun (username, password terenkripsi, metadata)
- Integrasi dengan SessionManagerV2
- Otomatis buat encryption key jika belum ada
- Aman untuk Termux & Windows

Dependensi:
  pip install cryptography python-dotenv
"""

import os
import json
import datetime
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from core.session_manager_v2 import SessionManagerV2

load_dotenv()

class AccountManager:
    def __init__(self, accounts_file="sessions/accounts.json", key_file=".secret.key"):
        self.accounts_file = accounts_file
        self.key_file = key_file
        os.makedirs(os.path.dirname(accounts_file), exist_ok=True)
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)
        self.session_manager = SessionManagerV2()

        if not os.path.exists(self.accounts_file):
            with open(self.accounts_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    # ====================================================
    # 🔐 ENCRYPTION
    # ====================================================
    def _load_or_generate_key(self) -> bytes:
        """Load encryption key atau buat baru"""
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
    # 🧠 ACCOUNT MANAGEMENT
    # ====================================================
    def add_account(self, username: str, password: str, note: str = ""):
        """Tambah akun baru ke database"""
        data = self._load_accounts()
        if username in data:
            print(f"⚠️ Akun '{username}' sudah ada.")
            return False

        enc_pass = self.encrypt(password)
        data[username] = {
            "password": enc_pass,
            "note": note,
            "added_at": datetime.datetime.utcnow().isoformat(),
        }

        self._save_accounts(data)
        print(f"✅ Akun '{username}' ditambahkan.")
        return True

    def remove_account(self, username: str):
        """Hapus akun dari database"""
        data = self._load_accounts()
        if username not in data:
            print(f"⚠️ Akun '{username}' tidak ditemukan.")
            return False
        del data[username]
        self._save_accounts(data)
        print(f"🗑️ Akun '{username}' dihapus.")
        return True

    def list_accounts(self):
        """Tampilkan semua akun"""
        data = self._load_accounts()
        if not data:
            print("📭 Belum ada akun.")
            return
        print("📂 Daftar Akun:")
        for user, info in data.items():
            note = info.get("note", "")
            print(f"  • {user} ({note})")

    def get_account_password(self, username: str) -> str:
        """Ambil password (dekripsi)"""
        data = self._load_accounts()
        if username not in data:
            raise ValueError(f"Akun '{username}' tidak ditemukan.")
        return self.decrypt(data[username]["password"])

    # ====================================================
    # ⚙️ FILE MANAGEMENT
    # ====================================================
    def _load_accounts(self) -> dict:
        try:
            with open(self.accounts_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ File akun korup, membuat ulang baru.")
            return {}

    def _save_accounts(self, data: dict):
        with open(self.accounts_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # ====================================================
    # 🌐 SESSION INTEGRATION
    # ====================================================
    def login_all(self):
        """Login semua akun yang tersimpan"""
        data = self._load_accounts()
        for username in data.keys():
            password = self.get_account_password(username)
            client = self.session_manager.load_session(username)
            if not client:
                print(f"🔑 Session baru dibuat untuk {username}.")
                client = self.session_manager.create_new_session(username, password)
            if client:
                self.session_manager.validate_session(username)

    # ====================================================
    # 📤 EXPORT / IMPORT
    # ====================================================
    def export_accounts(self, export_path="accounts_export.json"):
        data = self._load_accounts()
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"📤 Akun diekspor ke {export_path}")

    def import_accounts(self, import_path="accounts_export.json"):
        if not os.path.exists(import_path):
            print("⚠️ File import tidak ditemukan.")
            return
        with open(import_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._save_accounts(data)
        print("📥 Akun berhasil diimpor.")


if __name__ == "__main__":
    manager = AccountManager()
    print("\n=== Account Manager CLI ===")
    while True:
        print("\n1️⃣ Tambah akun\n2️⃣ Lihat akun\n3️⃣ Hapus akun\n4️⃣ Login semua\n5️⃣ Export akun\n6️⃣ Import akun\n0️⃣ Keluar")
        choice = input("Pilih opsi: ").strip()
        if choice == "1":
            u = input("Username: ")
            p = input("Password: ")
            n = input("Catatan (opsional): ")
            manager.add_account(u, p, n)
        elif choice == "2":
            manager.list_accounts()
        elif choice == "3":
            u = input("Username yang dihapus: ")
            manager.remove_account(u)
        elif choice == "4":
            manager.login_all()
        elif choice == "5":
            manager.export_accounts()
        elif choice == "6":
            manager.import_accounts()
        elif choice == "0":
            print("👋 Keluar.")
            break
        else:
            print("❌ Pilihan tidak valid.")