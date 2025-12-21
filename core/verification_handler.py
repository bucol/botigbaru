#!/usr/bin/env python3
"""
Verification Handler - Production Version

Handle semua jenis verifikasi Instagram:
- SMS code
- Email code
- Checkpoint / unusual activity
- 2FA (authenticator app)
- Security alert

Fitur:
- Deteksi tipe verifikasi dari error message
- Logging semua attempt ke JSONL
- Retry counting per akun
- Blacklist setelah max_retries
- Cooldown‑aware (bisa ditambah layer waktu di atasnya)
"""

import json
from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional


class VerificationType(Enum):
    SMS = "sms"
    EMAIL = "email"
    CHECKPOINT = "checkpoint"
    TWO_FA = "2fa"
    SECURITY_ALERT = "security_alert"
    UNKNOWN = "unknown"


class VerificationHandler:
    """
    Abstraction untuk semua verification flow.
    """

    def __init__(
        self,
        max_retries: int = 5,
        cooldown_minutes: int = 30,
        log_dir: str = "logs/verification_logs",
    ):
        self.max_retries = max_retries
        self.cooldown_minutes = cooldown_minutes
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    # ======================================================================
    # DETEKSI VERIFICATION TYPE
    # ======================================================================

    def detect_verification_required(self, error_message: str) -> Tuple[bool, VerificationType]:
        """
        Dari error_message (string apa pun), deteksi apakah ini verification,
        dan kalau iya, tipe verifikasinya apa.
        """
        if not error_message:
            return False, VerificationType.UNKNOWN

        msg = error_message.lower()

        # SMS
        sms_keywords = ["sms", "phone", "text message", "kode sms", "sent a code to", "via sms"]
        if any(k in msg for k in sms_keywords):
            return True, VerificationType.SMS

        # Email
        email_keywords = ["email", "mail", "sent a code to your email", "kode dikirim ke email"]
        if any(k in msg for k in email_keywords):
            return True, VerificationType.EMAIL

        # 2FA
        twofa_keywords = [
            "two factor",
            "2fa",
            "authentication app",
            "authenticator",
            "login code",
        ]
        if any(k in msg for k in twofa_keywords):
            return True, VerificationType.TWO_FA

        # Checkpoint / challenge
        checkpoint_keywords = [
            "checkpoint",
            "unusual activity",
            "suspicious login",
            "verify it’s you",
            "challenge_required",
        ]
        if any(k in msg for k in checkpoint_keywords):
            return True, VerificationType.CHECKPOINT

        # Security alert
        security_keywords = ["security alert", "suspicious attempt", "new login", "was this you"]
        if any(k in msg for k in security_keywords):
            return True, VerificationType.SECURITY_ALERT

        return False, VerificationType.UNKNOWN

    # ======================================================================
    # LOGGING / STORAGE
    # ======================================================================

    def _log_file_for_today(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"{today}.jsonl"

    def log_verification_attempt(
        self,
        username: str,
        verification_type: VerificationType,
        status: str,
        code_used: Optional[str] = None,
        message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Log satu verification attempt ke JSONL file.
        status: "pending" | "success" | "failed"
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "verification_type": verification_type.value,
            "status": status,
            "code_used": bool(code_used),
            "message": message or "",
        }

        try:
            log_file = self._log_file_for_today()
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "
")
        except Exception:
            # Jangan raise; verification tetap jalan walau logging gagal
            pass

        return log_entry

    # ======================================================================
    # RETRY COUNTING & BLACKLIST
    # ======================================================================

    def _iter_all_logs(self):
        """Internal: iterate semua log JSONL di folder."""
        if not self.log_dir.exists():
            return
        for file in sorted(self.log_dir.glob("*.jsonl")):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            yield json.loads(line)
                        except Exception:
                            continue
            except Exception:
                continue

    def get_retry_count(self, username: str) -> int:
        """
        Hitung berapa kali verification gagal untuk username ini (from all logs).
        """
        count = 0
        for entry in self._iter_all_logs():
            if (
                entry.get("username") == username
                and entry.get("status") == "failed"
            ):
                count += 1
        return count

    def is_blacklisted(self, username: str) -> bool:
        """
        True kalau user sudah melebihi max_retries gagal verification.
        """
        return self.get_retry_count(username) >= self.max_retries

    def get_verification_stats(self, username: str) -> Dict[str, Any]:
        """
        Return statistik sederhana untuk 1 akun:
        - total_attempts
        - failed_attempts
        - success_attempts
        - pending_count
        - last_status
        """
        total = failed = success = pending = 0
        last_status = None
        last_ts = None

        for entry in self._iter_all_logs():
            if entry.get("username") != username:
                continue

            total += 1
            status = entry.get("status")
            ts = entry.get("timestamp")

            if status == "failed":
                failed += 1
            elif status == "success":
                success += 1
            elif status == "pending":
                pending += 1

            if not last_ts or ts > last_ts:
                last_ts = ts
                last_status = status

        return {
            "total_attempts": total,
            "failed_attempts": failed,
            "success_attempts": success,
            "pending_count": pending,
            "last_status": last_status,
        }

    # ======================================================================
    # VERIFICATION FLOW (ABSTRAKSI SEDERHANA)
    # ======================================================================

    def handle_verification_flow(
        self,
        username: str,
        verification_type: VerificationType,
        auto_code: Optional[str] = None,
        manual_code: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Abstraksi high‑level:
        - Cek blacklist
        - Ambil kode (auto atau manual)
        - Log attempt sebagai success/failed

        Di sini TIDAK memanggil API Instagram langsung;
        integration sebenernya dilakukan di AccountManager/LoginManager.
        """

        # Cek blacklist
        if self.is_blacklisted(username):
            msg = (
                f"Akun {username} sudah mencapai batas maksimal percobaan "
                f"verifikasi ({self.max_retries}). Tunggu cooldown dulu."
            )
            self.log_verification_attempt(
                username, verification_type, "failed", message="blacklisted"
            )
            return False, msg

        # Ambil code
        code = auto_code or manual_code
        if not code:
            # Belum ada code, berarti hanya menandai pending
            self.log_verification_attempt(
                username, verification_type, "pending", message="waiting_for_code"
            )
            return False, "Verification code belum tersedia (pending)."

        # Di sini, secara real API harus dicall (misal: client.challenge_send(code))
        # Karena modul ini generic, kita "simulate" result, dan integration layer
        # yang akan decide success atau gagal sebenarnya.

        # Untuk sekarang: anggap code 6 digit numeric → success, lainnya → failed
        success = code.isdigit() and len(code) in (6, 8)

        status = "success" if success else "failed"
        self.log_verification_attempt(
            username,
            verification_type,
            status,
            code_used=code,
            message="auto_rule_check",
        )

        if success:
            return True, "Verification berhasil dengan code yang diberikan."
        else:
            # Bisa menyebabkan blacklist kalau gagal berkali‑kali
            if self.is_blacklisted(username):
                return (
                    False,
                    "Code salah dan akun sekarang masuk blacklist sementara "
                    f"(>{self.max_retries} gagal).",
                )
            return False, "Verification gagal, code tidak valid."


def create_verification_handler() -> VerificationHandler:
    """Factory kecil agar pemanggilan dari luar konsisten."""
    return VerificationHandler()