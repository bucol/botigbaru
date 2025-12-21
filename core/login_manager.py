#!/usr/bin/env python3
"""
Login Manager - Instagrapi Client Integration

Tugas:
- Buat instagrapi Client (optional proxy)
- Inject device identity (via SessionManagerV2)
- Jalankan login flow (client.login)
- Deteksi error & mapping ke verification flow
- Simpan session & update metadata akun
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    BadPassword,
    InvalidUser,
    CheckpointRequired,
    ChallengeRequired,
    TwoFactorRequired,
)

from .account_manager import AccountManager


class LoginManager:
    """
    Manage login flow dengan instagrapi Client
    """

    def __init__(self):
        self.account_manager = AccountManager()
        self.active_clients: Dict[str, Client] = {}

        self.login_log_dir = Path("logs/login_operations")
        self.login_log_dir.mkdir(parents=True, exist_ok=True)

        self.login_log_file = (
            self.login_log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        )

    # ======================================================================
    # LOGGING
    # ======================================================================

    def _log_login_event(
        self,
        username: str,
        event_type: str,
        status: str,
        details: Dict[str, Any] = None,
    ):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "event_type": event_type,
            "status": status,
            "details": details or {},
        }
        try:
            self.login_log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.login_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "
")
        except Exception:
            pass

    # ======================================================================
    # CLIENT CREATION
    # ======================================================================

    def create_client(self, use_proxy: bool = False, proxy_url: Optional[str] = None) -> Optional[Client]:
        """
        Buat instagrapi Client baru.
        """
        try:
            client = Client()

            if use_proxy and proxy_url:
                try:
                    client.set_proxy(proxy_url)
                except Exception as e:
                    print(f"⚠️ Error setting proxy: {e}")

            return client
        except Exception as e:
            print(f"❌ Error creating client: {e}")
            return None

    # ======================================================================
    # LOGIN FLOW
    # ======================================================================

    def login(
        self,
        username: str,
        password: str,
        use_proxy: bool = False,
        proxy_url: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[Client]]:
        """
        Complete login flow:
        - Pastikan account exist (kalau belum → register)
        - Buat instagrapi Client
        - Inject device identity
        - client.login(username, password)
        - Kalau butuh verification → balikin message
        - Kalau sukses → save session & mark as logged_in
        """
        if not isinstance(username, str) or not isinstance(password, str):
            return False, "Username/password invalid", None

        print(f"
🔐 Starting login for @{username}...")
        self._log_login_event(username, "login_start", "initiated")

        # Pastikan akun ada di AccountManager
        account_exists = username in self.account_manager.accounts_db

        if not account_exists:
            print("📝 Account belum terdaftar, registering...")
            reg_ok, reg_msg, _ = self.account_manager.register_account(
                username, self._hash_password(password)
            )
            if not reg_ok:
                self._log_login_event(
                    username, "account_registration", "failed", {"error": reg_msg}
                )
                return False, f"Registration failed: {reg_msg}", None
        else:
            print("✅ Account sudah ada, gunakan identity yang tersimpan")

        # Buat client
        print("🔧 Creating instagrapi client...")
        client = self.create_client(use_proxy=use_proxy, proxy_url=proxy_url)
        if not client:
            self._log_login_event(username, "client_creation", "failed")
            return False, "Failed to create instagrapi client", None

        # Ambil identity & inject
        device_identity = self.account_manager.identity_gen.get_or_create_identity(
            username
        )
        print(f"📱 Injecting device: {device_identity.get('model')}")

        inject_ok = self.account_manager.session_manager.inject_device_to_client(
            client, device_identity
        )
        if not inject_ok:
            print("⚠️ Device injection gagal, lanjut tetap coba login")

        self._log_login_event(
            username,
            "device_injected",
            "success",
            {
                "device_model": device_identity.get("model"),
                "device_id": device_identity.get("device_id"),
            },
        )

        # Attempt login
        print("🔑 Attempting login...")
        login_ok, login_msg = self._attempt_login(client, username, password)

        if not login_ok:
            # Coba lihat apakah ini verification-related
            verif_msg = self._handle_login_error(
                client, username, login_msg, device_identity
            )
            self._log_login_event(
                username,
                "login_attempt",
                "verification_required",
                {"error": login_msg, "verification_needed": True},
            )
            print(f"⚠️ Login membutuhkan verification: {verif_msg}")
            return False, verif_msg, client

        # Login sukses
        print("✅ Login berhasil!")
        self.active_clients[username] = client

        # Update metadata di AccountManager (tanpa calling client.login lagi)
        self.account_manager.login_account(
            username, self._hash_password(password), client=client
        )

        self._log_login_event(
            username,
            "login_success",
            "success",
            {"user_id": self._get_user_id(client)},
        )

        return True, "Login successful", client

    def _attempt_login(
        self,
        client: Client,
        username: str,
        password: str,
    ) -> Tuple[bool, str]:
        """
        Wrap client.login dengan error mapping menjadi string code.
        """
        try:
            client.login(username, password)
            return True, "OK"
        except BadPassword:
            return False, "BAD_PASSWORD: Password salah"
        except InvalidUser:
            return False, "INVALID_USER: Username tidak ditemukan"
        except CheckpointRequired:
            return False, "CHECKPOINT_REQUIRED: Checkpoint verification needed"
        except ChallengeRequired:
            return False, "CHALLENGE_REQUIRED: Challenge verification needed"
        except TwoFactorRequired:
            return False, "TWO_FACTOR_REQUIRED: 2FA verification needed"
        except LoginRequired:
            return False, "LOGIN_REQUIRED: Login required"
        except Exception as e:
            text = str(e).lower()
            if "checkpoint" in text or "unusual activity" in text:
                return False, "CHECKPOINT: Unusual activity detected"
            if "challenge" in text:
                return False, "CHALLENGE: Security challenge required"
            if "rate limit" in text or "too many" in text:
                return False, "RATE_LIMIT: Too many login attempts"
            if "sms" in text or "phone" in text:
                return False, "SMS_VERIFICATION: SMS verification needed"
            if "email" in text:
                return False, "EMAIL_VERIFICATION: Email verification needed"
            if "disabled" in text or "banned" in text:
                return False, "ACCOUNT_DISABLED: Account disabled/banned"
            return False, f"LOGIN_ERROR: {e}"

    def _handle_login_error(
        self,
        client: Client,
        username: str,
        error_msg: str,
        device_identity: Dict[str, Any],
    ) -> str:
        """
        Translate error_msg ke pesan user-friendly + trigger verification logging.
        """
        is_verif, vtype = self.account_manager.verification_handler.detect_verification_required(
            error_msg
        )

        if not is_verif:
            return error_msg

        # Log attempt pending
        self.account_manager.verification_handler.log_verification_attempt(
            username, vtype, "pending", message="login_verification_required"
        )

        if vtype == self.account_manager.verification_handler.__class__.VerificationType.SMS:
            # technically unreachable karena import alias, tapi biar jelas
            pass

        if vtype.value == "sms":
            return (
                "📱 SMS verification required.
"
                "Cek SMS yang dikirim ke nomor terdaftar, lalu input code nanti."
            )
        if vtype.value == "email":
            return (
                "📧 Email verification required.
"
                "Cek email dari Instagram dan input code ketika diminta."
            )
        if vtype.value == "checkpoint":
            return (
                "🔒 Checkpoint verification.
"
                "Buka aplikasi Instagram dan konfirmasi aktivitas login ini."
            )
        if vtype.value == "2fa":
            return (
                "🔐 2FA verification required.
"
                "Buka aplikasi authenticator dan masukkan 6-digit code."
            )
        if vtype.value == "security_alert":
            return (
                "🚨 Security alert.
"
                "Instagram mendeteksi login dari device/lokasi baru, "
                "konfirmasi di app atau email."
            )

        return f"Verification needed: {vtype.value}"

    # ======================================================================
    # MANUAL VERIFICATION CODE
    # ======================================================================

    def verify_code(self, username: str, code: str) -> Tuple[bool, str]:
        """
        Dipanggil saat user memasukkan verification code secara manual.
        Akan diteruskan ke AccountManager.handle_login_verification.
        """
        stats = self.account_manager.verification_handler.get_verification_stats(
            username
        )
        if stats.get("pending_count", 0) == 0:
            return False, "Tidak ada verification yang pending untuk akun ini."

        ok, msg, _ = self.account_manager.handle_login_verification(
            username,
            verification_error="manual_code_input",
            manual_code=code,
        )

        self._log_login_event(
            username,
            "verification_code_submit",
            "success" if ok else "failed",
            {"code_valid": ok},
        )

        return ok, msg

    # ======================================================================
    # LOGOUT & HELPERS
    # ======================================================================

    def logout(self, username: str) -> Tuple[bool, str]:
        """
        Logout client dari memory + clear session file.
        (Tidak memanggil client.logout() untuk menghindari extra noise ke IG,
        tapi bisa ditambahkan kalau mau lebih strict.)
        """
        if username not in self.active_clients:
            return False, "Client tidak aktif untuk username ini"

        # Optional: panggil client.logout() kalau mau benar‑benar logout dari IG
        client = self.active_clients[username]
        try:
            if hasattr(client, "logout"):
                client.logout()
        except Exception:
            pass

        del self.active_clients[username]
        self.account_manager.session_manager.clear_session(username)

        self._log_login_event(username, "logout", "success")
        return True, "Logout successful"

    def get_client(self, username: str) -> Optional[Client]:
        return self.active_clients.get(username)

    def is_logged_in(self, username: str) -> bool:
        return username in self.active_clients

    def get_logged_in_accounts(self):
        return list(self.active_clients.keys())

    # ======================================================================
    # UTILS
    # ======================================================================

    def _hash_password(self, password: str) -> str:
        """
        Hash sederhana (sha256). Untuk production sebaiknya pakai bcrypt/argon2.
        """
        import hashlib

        return hashlib.sha256(password.encode()).hexdigest()

    def _get_user_id(self, client: Client) -> Optional[str]:
        try:
            if hasattr(client, "user_id"):
                return str(client.user_id)
            if hasattr(client, "account_id"):
                return str(client.account_id)
        except Exception:
            return None
        return None

    def get_login_statistics(self) -> Dict[str, Any]:
        """
        Statistik sederhana untuk login manager:
        - total_active_sessions
        - logged_in_accounts (list)
        - account_manager_stats
        """
        return {
            "total_active_sessions": len(self.active_clients),
            "logged_in_accounts": self.get_logged_in_accounts(),
            "account_manager_stats": self.account_manager.get_statistics(),
        }


def create_login_manager() -> LoginManager:
    return LoginManager()