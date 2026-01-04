#!/usr/bin/env python3
"""
Session Manager v2 - Production Fixed Version

Tugas:
- Membuat session object per akun (termasuk device identity & instagrapi Client)
- Simpan / muat / hapus session dari file JSON
- Tangani auto-relogin bila session invalid
- Aman untuk Termux & Windows

Dependensi:
  pip install instagrapi python-dotenv
"""

import os
import json
import time
import random
from datetime import datetime
from typing import Optional
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    PleaseWaitFewMinutes,
    TwoFactorRequired,
)
from dotenv import load_dotenv

# Local imports
from core.device_identity_generator import DeviceIdentityGenerator

load_dotenv()

class SessionManagerV2:
    def __init__(self, sessions_dir="sessions"):
        self.sessions_dir = sessions_dir
        self.device_gen = DeviceIdentityGenerator()
        os.makedirs(sessions_dir, exist_ok=True)
        self.client = None

    def _get_session_path(self, username: str) -> str:
        """Generate JSON path for session file"""
        return os.path.join(self.sessions_dir, f"{username}_session.json")

    def create_new_session(self, username: str, password: str) -> Client:
        """Login dan buat session baru"""
        client = Client()

        # Generate & inject device identity
        device_identity = self.device_gen.generate_identity()
        client.set_device(
            {
                "manufacturer": device_identity["manufacturer"],
                "model": device_identity["model"],
                "device": device_identity["device"],
                "android_version": device_identity["android_version"],
            }
        )

        try:
            print(f"[LOGIN] Attempting login for {username}...")
            client.login(username, password)
            print(f"✅ Login successful for {username}")
            self.save_session(client, username)
            return client
        except TwoFactorRequired:
            print("⚠️ Two-factor authentication required. Please complete it manually.")
        except ChallengeRequired:
            print("⚠️ Instagram challenge required — verify in app.")
        except PleaseWaitFewMinutes:
            print("⏳ Rate limited by Instagram, please wait a few minutes.")
        except Exception as e:
            print(f"❌ Login failed for {username}: {e}")
        return None

    def load_session(self, username: str) -> Optional[Client]:
        """Load session dari file JSON, auto relog kalau invalid"""
        session_path = self._get_session_path(username)
        client = Client()

        if not os.path.exists(session_path):
            print(f"⚠️ Session file not found for {username}. Please login first.")
            return None

        try:
            client.load_settings(session_path)
            client.login(username, os.getenv("IG_PASSWORD", ""))
            print(f"✅ Session loaded for {username}")
            self.client = client
            return client
        except LoginRequired:
            print(f"⚠️ Session expired for {username}, relogging...")
            password = os.getenv("IG_PASSWORD", "")
            return self.create_new_session(username, password)
        except Exception as e:
            print(f"❌ Failed to load session for {username}: {e}")
            return None

    def save_session(self, client: Client, username: str):
        """Simpan session JSON"""
        session_path = self._get_session_path(username)
        try:
            client.dump_settings(session_path)
            print(f"💾 Session saved to {session_path}")
        except Exception as e:
            print(f"❌ Failed to save session: {e}")

    def clear_session(self, username: str):
        """Hapus session file"""
        session_path = self._get_session_path(username)
        if os.path.exists(session_path):
            os.remove(session_path)
            print(f"🧹 Session for {username} cleared.")
        else:
            print(f"⚠️ No session found for {username}.")

    def validate_session(self, username: str) -> bool:
        """Validasi apakah session masih aktif"""
        client = self.load_session(username)
        if not client:
            return False
        try:
            client.get_timeline_feed()
            print(f"✅ Session for {username} is active.")
            return True
        except LoginRequired:
            print(f"⚠️ Session expired for {username}.")
            return False
        except Exception as e:
            print(f"❌ Error validating session for {username}: {e}")
            return False


if __name__ == "__main__":
    sm = SessionManagerV2()
    username = input("Masukkan username IG: ")
    password = input("Masukkan password IG: ")
    client = sm.create_new_session(username, password)
    if client:
        sm.validate_session(username)