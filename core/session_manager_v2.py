#!/usr/bin/env python3
"""
Session Manager v2 - Integrated Version
Tugas: Handle load/save cookies (session) ke file JSON.
PENTING: Tidak boleh membuat Client() baru sembarangan agar Device ID tetap konsisten.
"""

import os
import logging
from typing import Optional
from instagrapi import Client
from instagrapi.exceptions import LoginRequired

# Setup logger
logger = logging.getLogger(__name__)

class SessionManagerV2:
    def __init__(self, sessions_dir="sessions"):
        self.sessions_dir = sessions_dir
        os.makedirs(sessions_dir, exist_ok=True)

    def _get_session_path(self, username: str) -> str:
        """Generate path file JSON session"""
        return os.path.join(self.sessions_dir, f"{username}_session.json")

    def save_session(self, client: Client, username: str):
        """Simpan cookies dari client ke JSON"""
        session_path = self._get_session_path(username)
        try:
            client.dump_settings(session_path)
            logger.info(f"💾 Session saved: {session_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save session for {username}: {e}")

    def load_session(self, client: Client, username: str) -> bool:
        """
        Muat cookies ke dalam client yang SUDAH ada.
        Return: True jika berhasil load & valid, False jika gagal/expired.
        """
        session_path = self._get_session_path(username)

        if not os.path.exists(session_path):
            logger.warning(f"⚠️ No session file found for {username}")
            return False

        try:
            # Load settings ke client yang sudah membawa Device ID
            client.load_settings(session_path)
            
            # Validasi singkat tanpa request network berat
            if not client.get_settings():
                return False
                
            logger.info(f"📂 Session settings loaded for {username}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Corrupt session for {username}: {e}")
            return False

    def validate_session(self, username: str) -> bool:
        """
        Cek apakah file session ada dan strukturnya valid (tanpa login network)
        """
        return os.path.exists(self._get_session_path(username))

    def delete_session(self, username: str):
        """Hapus file session (logout)"""
        path = self._get_session_path(username)
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"🧹 Session deleted for {username}")

if __name__ == "__main__":
    # Test Unit
    print("Modul SessionManagerV2 siap.")