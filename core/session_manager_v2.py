#!/usr/bin/env python3
"""
Session Manager v2 - Production Version

Fokus:
- Buat session object per akun (termasuk device_identity & config instagrapi)
- Save / load / clear session ke file JSON
- Inject device identity ke instagrapi Client
- Auto clear session + identity saat password change
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class SessionManagerV2:
    """
    Session manager untuk akun Instagram:
    - Satu file session per akun: sessions/account_sessions/<username>.json
    - Device identity disimpan terpisah (di-handle DeviceIdentityGenerator)
    """

    def __init__(self):
        self.session_dir = Path("sessions/account_sessions")
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.session_log_dir = Path("data/session_logs")
        self.session_log_dir.mkdir(parents=True, exist_ok=True)

    # ======================================================================
    # PATH HELPERS
    # ======================================================================

    def _session_path(self, username: str) -> Path:
        safe = "".join(c for c in username if c.isalnum() or c in ("_", "-", "."))
        return self.session_dir / f"{safe}.json"

    def _log_file_for_today(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.session_log_dir / f"{today}.jsonl"

    def _log_event(self, username: str, event: str, details: Dict[str, Any] = None):
        """Log event session ke JSONL (for audit)."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "event": event,
            "details": details or {},
        }
        try:
            log_file = self._log_file_for_today()
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "
")
        except Exception:
            # Logging gagal tidak boleh stop flow
            pass

    # ======================================================================
    # CREATE / SAVE / LOAD / CLEAR
    # ======================================================================

    def create_session(self, username: str, device_identity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Buat session object baru dengan session_id unik + attach device_identity.
        """
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        session = {
            "username": username,
            "session_id": session_id,
            "created_at": now,
            "updated_at": now,
            "device_identity": device_identity,
            "instagrapi_config": {
                "headers": {},
                "proxy": None,
            },
        }

        self._log_event(username, "session_created", {"session_id": session_id})
        return session

    def save_session(self, username: str, session: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Save session ke file JSON. Return (success, filepath).
        """
        path = self._session_path(username)
        try:
            session["updated_at"] = datetime.now().isoformat()
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(session, f, indent=2, ensure_ascii=False)
            self._log_event(username, "session_saved", {"session_file": str(path)})
            return True, str(path)
        except Exception as e:
            self._log_event(username, "session_save_error", {"error": str(e)})
            return False, str(e)

    def load_session(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Load session dari file. Return None kalau tidak ada / invalid.
        """
        path = self._session_path(username)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                session = json.load(f)
            return session
        except Exception as e:
            self._log_event(username, "session_load_error", {"error": str(e)})
            return None

    def clear_session(self, username: str) -> Tuple[bool, str]:
        """
        Delete session file untuk username ini.
        """
        path = self._session_path(username)
        if not path.exists():
            return True, "No session file"

        try:
            path.unlink()
            self._log_event(username, "session_cleared", {"session_file": str(path)})
            return True, "Session cleared"
        except Exception as e:
            self._log_event(username, "session_clear_error", {"error": str(e)})
            return False, str(e)

    # ======================================================================
    # DEVICE INJECTION KE INSTAGRAPI CLIENT
    # ======================================================================

    def inject_device_to_client(self, client: Any, device_identity: Dict[str, Any]) -> bool:
        """
        Inject device identity ke instagrapi Client:
        - Set device dan user agent
        - Tambah custom headers untuk fingerprint
        """
        try:
            # Basic mapping ke client
            if hasattr(client, "set_device"):
                # Banyak implementasi instagrapi pakai dict seperti ini
                device_settings = {
                    "manufacturer": device_identity.get("manufacturer"),
                    "model": device_identity.get("model"),
                    "android_version": device_identity.get("android_version", 12),
                    "android_release": str(device_identity.get("android_version", 12)),
                    "cpu": device_identity.get("cpu"),
                    "hardware": device_identity.get("device"),
                    "device": device_identity.get("device"),
                    "product": device_identity.get("product"),
                }
                client.set_device(device_settings)

            # Custom user agent (opsional, tergantung instagrapi)
            if hasattr(client, "set_user_agent"):
                brand = device_identity.get("brand", "samsung")
                model = device_identity.get("model", "SM-G991B")
                android_ver = device_identity.get("android_version", 12)
                ua = f"Instagram 300.0.0.0 Android ({android_ver}/12; 480dpi; 1080x1920; {brand}; {model}; {model}; qcom; en_US)"
                client.set_user_agent(ua)

            # Headers untuk fingerprint
            try:
                headers = getattr(client, "session", None)
                if headers and hasattr(headers, "headers"):
                    headers.headers.update(
                        {
                            "X-Device-ID": device_identity.get("device_id", ""),
                            "X-Android-ID": device_identity.get("android_id", ""),
                            "X-GSF-ID": device_identity.get("gsf_id", ""),
                            "X-IMEI": device_identity.get("imei_1", ""),
                            "X-Serial": device_identity.get("serial_number", ""),
                            "X-Fingerprint": device_identity.get("fingerprint", ""),
                        }
                    )
            except Exception:
                # Kalau gagal update headers, tidak fatal
                pass

            return True
        except Exception as e:
            # Logging generic, tapi jangan hentikan program
            self._log_event(
                device_identity.get("username", "unknown"),
                "device_injection_error",
                {"error": str(e)},
            )
            return False

    # ======================================================================
    # PASSWORD CHANGE FLOW (AUTO CLEAR)
    # ======================================================================

    def on_password_changed(self, username: str) -> Dict[str, Any]:
        """
        Dipanggil kalau password akun ini diganti.
        Strategy:
        - Clear session file (supaya next login fresh)
        - Clear identity file (biar device regenerate)
        NOTE: penghapusan identity file dilakukan di AccountManager/DeviceIdentityGenerator,
        tapi di sini kita tetap log action yang relevan.
        """
        actions = []

        cleared, msg = self.clear_session(username)
        actions.append(
            {
                "action": "session_cleared",
                "success": cleared,
                "message": msg,
            }
        )

        # Identity dihapus di level lain; kita cuma log niatnya
        actions.append(
            {
                "action": "identity_cleared",
                "success": True,
                "message": "Identity akan dire-generate oleh DeviceIdentityGenerator",
            }
        )

        self._log_event(username, "password_changed_flow", {"actions": actions})

        return {
            "success": True,
            "username": username,
            "actions": actions,
        }

    # ======================================================================
    # STATISTICS
    # ======================================================================

    def get_session_statistics(self) -> Dict[str, Any]:
        """
        Statistik sederhana:
        - total_sessions_files
        - usernames (list)
        """
        usernames = []
        if self.session_dir.exists():
            for file in self.session_dir.glob("*.json"):
                usernames.append(file.stem)

        return {
            "total_session_files": len(usernames),
            "usernames": usernames,
        }


def create_session_manager_v2() -> SessionManagerV2:
    """Factory kecil untuk konsistensi import."""
    return SessionManagerV2()