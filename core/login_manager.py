#!/usr/bin/env python3
"""
Login Manager - Production Fixed Version

Tugas:
- Login dan manajemen akun (multi account)
- Integrasi dengan SessionManagerV2 dan VerificationHandler
- Handle expired session, challenge, dan rate limit
- Kompatibel untuk Termux & Windows

Dependensi:
  pip install instagrapi python-dotenv
"""

import os
import time
import random
from datetime import datetime
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    TwoFactorRequired,
    PleaseWaitFewMinutes,
)

# local imports
from core.session_manager_v2 import SessionManagerV2
from core.verification_handler import VerificationHandler
from core.account_manager import AccountManager

load_dotenv()


class LoginManager:
    def __init__(self):
        self.session_manager = SessionManagerV2()
        self.verifier = VerificationHandler()
        self.account_manager = AccountManager()
        self.max_retries = 3

    # ====================================================
    # 🔑 LOGIN PER AKUN
    # ====================================================
    def login(self, username: str, password: str) -> Client | None:
        """
        Login satu akun dengan full handler
        """
        client = self.session_manager.load_session(username)
        if client:
            print(f"✅ Session ditemukan untuk {username}")
            try:
                client.get_timeline_feed()
                print(f"✅ Session {username} masih aktif.")
                return client
            except LoginRequired:
                print(f"⚠️ Session expired untuk {username}. Relogin...")
            except Exception as e:
                print(f"⚠️ Error saat cek session {username}: {e}")

        for attempt in range(self.max_retries):
            try:
                print(f"🔑 Login attempt {attempt+1}/{self.max_retries} untuk {username}")
                client = Client()
                client.login(username, password)
                print(f"✅ Login sukses untuk {username}")
                self.session_manager.save_session(client, username)
                return client

            except TwoFactorRequired:
                print(f"🔐 TwoFactorRequired untuk {username}")
                client = self.verifier.handle_two_factor(client, username, password)
                if client:
                    self.session_manager.save_session(client, username)
                    return client

            except ChallengeRequired:
                print(f"⚠️ ChallengeRequired untuk {username}")
                client = self.verifier.handle_challenge(client, username)
                if client:
                    self.session_manager.save_session(client, username)
                    return client

            except PleaseWaitFewMinutes:
                delay = random.randint(60, 180)
                print(f"⏳ Rate limited. Menunggu {delay}s sebelum coba lagi...")
                time.sleep(delay)

            except Exception as e:
                print(f"❌ Gagal login {username}: {e}")
                time.sleep(random.randint(5, 15))

        print(f"❌ Semua percobaan login gagal untuk {username}")
        return None

    # ====================================================
    # 🔁 LOGIN SEMUA AKUN
    # ====================================================
    def login_all_accounts(self):
        """
        Loop semua akun dari AccountManager
        """
        data = self.account_manager._load_accounts()
        if not data:
            print("📭 Tidak ada akun tersimpan.")
            return

        for username in data:
            password = self.account_manager.get_account_password(username)
            print(f"\n👤 Login akun: {username}")
            client = self.login(username, password)
            if client:
                print(f"✅ {username} aktif & tersambung.\n")
                self.session_manager.validate_session(username)
            else:
                print(f"❌ Gagal login akun {username}.\n")

    # ====================================================
    # 🧹 LOGOUT & RESET SESSION
    # ====================================================
    def logout_account(self, username: str):
        path = self.session_manager._get_session_path(username)
        if os.path.exists(path):
            os.remove(path)
            print(f"🧹 Session {username} dihapus.")
        else:
            print(f"⚠️ Session {username} tidak ditemukan.")

    def logout_all(self):
        data = self.account_manager._load_accounts()
        for username in data:
            self.logout_account(username)
        print("✅ Semua session dihapus.")

    # ====================================================
    # 🧠 UTILITIES
    # ====================================================
    def check_status(self, username: str):
        """
        Periksa status session akun tertentu
        """
        active = self.session_manager.validate_session(username)
        if active:
            print(f"✅ {username} masih aktif.")
        else:
            print(f"⚠️ {username} butuh login ulang.")


if __name__ == "__main__":
    manager = LoginManager()
    print("\n=== Login Manager CLI ===")
    while True:
        print("\n1️⃣ Login semua akun\n2️⃣ Cek status akun\n3️⃣ Hapus session\n4️⃣ Hapus semua session\n0️⃣ Keluar")
        choice = input("Pilih opsi: ").strip()
        if choice == "1":
            manager.login_all_accounts()
        elif choice == "2":
            user = input("Username: ").strip()
            manager.check_status(user)
        elif choice == "3":
            user = input("Username: ").strip()
            manager.logout_account(user)
        elif choice == "4":
            manager.logout_all()
        elif choice == "0":
            print("👋 Keluar dari Login Manager.")
            break
        else:
            print("❌ Pilihan tidak valid.")