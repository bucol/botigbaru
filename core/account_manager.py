#!/usr/bin/env python3
"""
Account Manager - Integration Module

Gabungkan:
- DeviceIdentityGenerator
- VerificationHandler
- SessionManagerV2

Tugas:
- Register akun baru
- Login akun (tanpa langsung call instagrapi, itu di LoginManager)
- Handle verification status
- Handle password change (auto clear session/identity)
- Simpel statistics & logging
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from .device_identity_generator import DeviceIdentityGenerator
from .verification_handler import VerificationHandler, VerificationType
from .session_manager_v2 import SessionManagerV2


class AccountManager:
    """
    Master manager untuk lifecycle akun.
    """

    def __init__(self):
        self.identity_gen = DeviceIdentityGenerator()
        self.verification_handler = VerificationHandler()
        self.session_manager = SessionManagerV2()

        self.accounts_db_file = Path("data/accounts_db.json")
        self.accounts_db_file.parent.mkdir(parents=True, exist_ok=True)

        self.accounts_db: Dict[str, Any] = self._load_accounts_db()

        self.account_log_dir = Path("logs/account_operations")
        self.account_log_dir.mkdir(parents=True, exist_ok=True)

    # ======================================================================
    # INTERNAL HELPERS
    # ======================================================================

    def _load_accounts_db(self) -> Dict[str, Any]:
        try:
            if self.accounts_db_file.exists():
                with open(self.accounts_db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
        except Exception:
            pass
        return {}

    def _save_accounts_db(self) -> None:
        try:
            self.accounts_db_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.accounts_db_file, "w", encoding="utf-8") as f:
                json.dump(self.accounts_db, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _log_operation(
        self,
        operation: str,
        username: str,
        status: str,
        details: Dict[str, Any] = None,
    ):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "username": username,
            "status": status,
            "details": details or {},
        }
        try:
            log_file = self.account_log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "
")
        except Exception:
            pass

    # ======================================================================
    # PUBLIC API: REGISTER / LOGIN / PASSWORD
    # ======================================================================

    def register_account(
        self, username: str, password_hash: str, email: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Register akun baru:
        - Cek duplicate
        - Generate device identity
        - Create session object
        - Simpan metadata ke accounts_db
        """
        if not isinstance(username, str) or not username:
            return False, "Username invalid", {}

        if username in self.accounts_db:
            return False, f"Akun {username} sudah terdaftar", {}

        try:
            # Device identity
            device_identity = self.identity_gen.get_or_create_identity(username)

            # Session
            session = self.session_manager.create_session(username, device_identity)
            self.session_manager.save_session(username, session)

            account_data = {
                "username": username,
                "password_hash": password_hash,
                "email": email,
                "registered_at": datetime.now().isoformat(),
                "device_id": device_identity.get("device_id"),
                "device_model": device_identity.get("model"),
                "status": "active",
                "session_id": session.get("session_id"),
                "verification_status": "pending",
                "last_login": None,
            }

            self.accounts_db[username] = account_data
            self._save_accounts_db()

            self._log_operation(
                "account_registered",
                username,
                "success",
                {
                    "device_model": device_identity.get("model"),
                    "device_id": device_identity.get("device_id"),
                },
            )

            result = {
                "username": username,
                "device_identity": device_identity,
                "session": session,
            }
            return True, "Account registered successfully", result

        except Exception as e:
            self._log_operation(
                "account_register_failed",
                username,
                "failed",
                {"error": str(e)},
            )
            return False, f"Error registering account: {e}", {}

    def login_account(
        self, username: str, password_hash: str, client: Any = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Login akun secara internal (tanpa call client.login di sini):
        - Pastikan akun exist
        - Load/generate device identity
        - Create & save session
        - Inject device ke client (kalau diberikan)
        - Update last_login & session_id
        """
        if username not in self.accounts_db:
            return False, f"Akun {username} tidak ditemukan", {}

        try:
            account_data = self.accounts_db[username]

            if account_data.get("password_hash") != password_hash:
                return False, "Password hash tidak cocok", {}

            # Identity
            device_identity = self.identity_gen.load_identity(username)
            if not device_identity:
                device_identity = self.identity_gen.get_or_create_identity(username)

            # Session
            session = self.session_manager.create_session(username, device_identity)
            self.session_manager.save_session(username, session)

            # Optional: inject ke client
            if client is not None:
                self.session_manager.inject_device_to_client(client, device_identity)

            # Update account DB
            account_data["last_login"] = datetime.now().isoformat()
            account_data["session_id"] = session.get("session_id")
            self._save_accounts_db()

            self._log_operation(
                "account_login",
                username,
                "success",
                {
                    "device_model": device_identity.get("model"),
                    "session_id": session.get("session_id"),
                },
            )

            result = {
                "username": username,
                "device_identity": device_identity,
                "session": session,
            }
            return True, "Login metadata updated", result

        except Exception as e:
            self._log_operation(
                "account_login_failed",
                username,
                "failed",
                {"error": str(e)},
            )
            return False, f"Error login account: {e}", {}

    def change_password(
        self, username: str, new_password_hash: str
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Dipanggil setelah password IG diganti:
        - Update password_hash di DB
        - Trigger session_manager.on_password_changed (auto clear session)
        - Hapus identity file (biar regenerate next login)
        """
        if username not in self.accounts_db:
            return False, f"Akun {username} tidak ditemukan", {}

        try:
            self.accounts_db[username]["password_hash"] = new_password_hash
            self._save_accounts_db()

            # Session flow
            flow_result = self.session_manager.on_password_changed(username)

            # Delete identity file
            identity_deleted = self.identity_gen.delete_identity(username)

            self._log_operation(
                "password_changed",
                username,
                "success",
                {
                    "flow_result": flow_result,
                    "identity_deleted": identity_deleted,
                },
            )

            result = {
                "flow_result": flow_result,
                "identity_deleted": identity_deleted,
            }
            return True, "Password updated and session cleared", result

        except Exception as e:
            self._log_operation(
                "password_change_failed",
                username,
                "failed",
                {"error": str(e)},
            )
            return False, f"Error changing password: {e}", {}

    # ======================================================================
    # VERIFICATION INTEGRATION
    # ======================================================================

    def handle_login_verification(
        self,
        username: str,
        verification_error: str,
        auto_code: Optional[str] = None,
        manual_code: Optional[str] = None,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Dipanggil dari LoginManager kalau login gagal karena verification.
        - Deteksi tipe verification dari error string
        - Cek blacklist
        - Jalankan verification_handler.handle_verification_flow
        - Update verification_status di account DB kalau sukses
        """
        if username not in self.accounts_db:
            return False, f"Akun {username} tidak ditemukan", {}

        # Deteksi tipe
        is_verif, vtype = self.verification_handler.detect_verification_required(
            verification_error
        )
        if not is_verif:
            return False, "Verification tidak terdeteksi dari error ini", {}

        # Jalankan flow (kode bisa auto/manual)
        ok, msg = self.verification_handler.handle_verification_flow(
            username,
            vtype,
            auto_code=auto_code,
            manual_code=manual_code,
        )

        if ok:
            self.accounts_db[username]["verification_status"] = "verified"
            self._save_accounts_db()

            self._log_operation(
                "verification_success",
                username,
                "success",
                {
                    "verification_type": vtype.value,
                    "code_provided": bool(auto_code or manual_code),
                },
            )

            return True, msg, {
                "username": username,
                "verification_type": vtype.value,
                "status": "verified",
            }
        else:
            # Kalau gagal, cek apakah masuk blacklist
            if self.verification_handler.is_blacklisted(username):
                self.accounts_db[username]["status"] = "blacklisted"
                self._save_accounts_db()
                self._log_operation(
                    "account_blacklisted",
                    username,
                    "failed",
                    {"reason": "verification_max_retries"},
                )

            self._log_operation(
                "verification_failed",
                username,
                "failed",
                {
                    "verification_type": vtype.value,
                    "message": msg,
                },
            )

            return False, msg, {}

    # ======================================================================
    # INFORMATION / STATISTICS
    # ======================================================================

    def get_account_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Return info lengkap untuk satu akun, termasuk ringkasan device & verification stats.
        """
        if username not in self.accounts_db:
            return None

        base = self.accounts_db[username].copy()

        # Tambah ringkasan device
        identity = self.identity_gen.load_identity(username)
        if identity:
            base["device_identity_summary"] = {
                "model": identity.get("model"),
                "brand": identity.get("brand"),
                "android_version": identity.get("android_version"),
                "device_id": identity.get("device_id"),
                "imei_1": identity.get("imei_1"),
            }
        else:
            base["device_identity_summary"] = None

        # Tambah verification stats
        base["verification_stats"] = self.verification_handler.get_verification_stats(
            username
        )

        return base

    def list_all_accounts(self) -> Dict[str, Any]:
        """
        List semua akun yang tersimpan.
        """
        return {
            "total": len(self.accounts_db),
            "accounts": list(self.accounts_db.keys()),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """
        Statistik global akun:
        - total_accounts
        - active_accounts
        - blacklisted_accounts
        - verified_accounts
        """
        total = len(self.accounts_db)
        active = 0
        blacklisted = 0
        verified = 0

        for data in self.accounts_db.values():
            if data.get("status") == "active":
                active += 1
            if data.get("status") == "blacklisted":
                blacklisted += 1
            if data.get("verification_status") == "verified":
                verified += 1

        return {
            "total_accounts": total,
            "active_accounts": active,
            "blacklisted_accounts": blacklisted,
            "verified_accounts": verified,
        }


def create_account_manager() -> AccountManager:
    """Factory kecil biar import dari luar konsisten."""
    return AccountManager()