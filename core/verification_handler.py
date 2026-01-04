#!/usr/bin/env python3
"""
Verification Handler - Production Fixed Version

Tugas:
- Tangani ChallengeRequired (kode verifikasi via email/SMS)
- Tangani TwoFactorRequired (2FA login)
- Auto retry login bila gagal
- Kompatibel dengan Termux & Windows

Dependensi:
  pip install instagrapi python-dotenv
"""

import os
import time
import random
from datetime import datetime
from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    TwoFactorRequired,
    PleaseWaitFewMinutes,
    LoginRequired,
)
from dotenv import load_dotenv

load_dotenv()


class VerificationHandler:
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_delay = 10  # detik

    # =====================================================
    # 🔐 TWO FACTOR AUTH HANDLER
    # =====================================================
    def handle_two_factor(self, client: Client, username: str, password: str):
        """
        Tangani Two-Factor Authentication (2FA)
        """
        print(f"🔐 Two-factor authentication diperlukan untuk akun: {username}")
        try:
            code = input("Masukkan kode 2FA (dari SMS / App Authenticator): ").strip()
            result = client.two_factor_login(username, password, code)
            if result:
                print("✅ Two-factor login berhasil.")
                return client
        except Exception as e:
            print(f"❌ Gagal 2FA login: {e}")
        return None

    # =====================================================
    # ⚙️ CHALLENGE HANDLER
    # =====================================================
    def handle_challenge(self, client: Client, username: str):
        """
        Tangani ChallengeRequired (verifikasi via email/SMS)
        """
        print(f"⚠️ Challenge login diperlukan untuk akun: {username}")

        try:
            challenge_info = client.challenge_resolve()
            if challenge_info.get("step_name") == "select_verify_method":
                choice = input("Verifikasi via (1) Email, (2) SMS ? [1/2]: ").strip()
                selected = "1" if choice == "1" else "0"
                client.challenge_select_verify_method(selected)
                print("✅ Metode verifikasi dikirim.")
                time.sleep(3)

            code = input("Masukkan kode verifikasi (dari email/SMS): ").strip()
            result = client.challenge_send_security_code(code)
            if result:
                print("✅ Challenge berhasil diverifikasi.")
                return client
            else:
                print("❌ Challenge gagal diverifikasi.")
        except Exception as e:
            print(f"❌ Gagal handle challenge: {e}")

        return None

    # =====================================================
    # 🔁 RETRY MECHANISM
    # =====================================================
    def safe_login(self, username: str, password: str):
        """
        Coba login dengan handling challenge dan 2FA otomatis
        """
        client = Client()
        for attempt in range(self.max_retries):
            try:
                print(f"🔑 Login attempt {attempt + 1}/{self.max_retries} untuk {username}")
                client.login(username, password)
                print("✅ Login sukses tanpa challenge.")
                return client

            except TwoFactorRequired:
                print("🔐 Two-factor authentication terdeteksi.")
                return self.handle_two_factor(client, username, password)

            except ChallengeRequired:
                print("⚠️ ChallengeRequired terdeteksi.")
                return self.handle_challenge(client, username)

            except PleaseWaitFewMinutes:
                print("⏳ Instagram membatasi login. Menunggu 2 menit...")
                time.sleep(120)

            except LoginRequired:
                print("⚠️ LoginRequired, mencoba ulang...")
                time.sleep(self.retry_delay)

            except Exception as e:
                print(f"❌ Error login: {e}")
                time.sleep(self.retry_delay + random.randint(3, 10))

        print("❌ Semua percobaan login gagal.")
        return None


if __name__ == "__main__":
    handler = VerificationHandler()
    username = input("Masukkan username IG: ").strip()
    password = input("Masukkan password IG: ").strip()
    client = handler.safe_login(username, password)
    if client:
        print("✅ Login berhasil dan client aktif.")
    else:
        print("❌ Gagal login.")