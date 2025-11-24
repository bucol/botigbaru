#!/usr/bin/env python3
"""
Verification Handler - SMS, Email, Checkpoint, 2FA
Support: auto OTP parsing + manual input + retry tracking
Production-grade dengan error handling & safe file operations
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, Optional
from pathlib import Path
from enum import Enum

class VerificationType(Enum):
    """Tipe verification yang bisa di-trigger Instagram"""
    SMS = "sms"
    EMAIL = "email"
    CHECKPOINT = "checkpoint"
    TWO_FA = "2fa"
    SECURITY_ALERT = "security_alert"
    UNKNOWN = "unknown"

class VerificationHandler:
    """Handle semua jenis verification saat login (production-safe)"""
    
    def __init__(self, max_retries: int = 5, cooldown_minutes: int = 30):
        self.max_retries = max_retries
        self.cooldown_minutes = cooldown_minutes
        self.verification_log_dir = Path('data/verification_logs')
        self.verification_log_file = self.verification_log_dir / 'verification_attempts.jsonl'
        self.blacklist_file = Path('data/blacklist_accounts.json')
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create semua directory (safe cross-platform)"""
        try:
            self.verification_log_dir.mkdir(parents=True, exist_ok=True)
            Path('data').mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️ Warning creating directories: {e}")
    
    def detect_verification_required(self, error_msg: str) -> Tuple[bool, VerificationType]:
        """
        Deteksi tipe verification dari error message instagrapi
        Return: (is_verification_required, verification_type)
        """
        try:
            if not isinstance(error_msg, str):
                return False, VerificationType.UNKNOWN
            
            error_lower = error_msg.lower()
            
            # Priority order: specific to general
            if any(x in error_lower for x in ['sms', 'phone', 'text message']):
                return True, VerificationType.SMS
            elif any(x in error_lower for x in ['checkpoint', 'unusual activity', 'try later']):
                return True, VerificationType.CHECKPOINT
            elif any(x in error_lower for x in ['2fa', 'two factor', 'authenticator', 'totp']):
                return True, VerificationType.TWO_FA
            elif any(x in error_lower for x in ['email', 'confirm', 'verify email']):
                return True, VerificationType.EMAIL
            elif any(x in error_lower for x in ['security', 'alert', 'suspicious']):
                return True, VerificationType.SECURITY_ALERT
            
            return False, VerificationType.UNKNOWN
        
        except Exception as e:
            print(f"❌ Error detecting verification: {e}")
            return False, VerificationType.UNKNOWN
    
    def log_verification_attempt(self, username: str, verification_type: VerificationType,
                                  status: str, code_provided: Optional[str] = None,
                                  error_detail: Optional[str] = None) -> Dict[str, Any]:
        """
        Log setiap verification attempt (safe append to JSONL)
        status: 'pending', 'success', 'failed', 'blacklist', 'expired'
        """
        try:
            # Validate inputs
            if not isinstance(username, str) or len(username) == 0:
                raise ValueError("Username invalid")
            
            if not isinstance(status, str):
                status = 'unknown'
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'verification_type': verification_type.value if isinstance(verification_type, VerificationType) else str(verification_type),
                'status': status,
                'code_provided': bool(code_provided),  # Jangan log code langsung (security)
                'error_detail': str(error_detail) if error_detail else None
            }
            
            # Append to JSONL (safe append mode)
            with open(self.verification_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            return log_entry
        
        except Exception as e:
            print(f"❌ Error logging verification: {e}")
            return {}
    
    def get_retry_count(self, username: str) -> int:
        """Hitung berapa kali akun verification FAIL"""
        try:
            if not self.verification_log_file.exists():
                return 0
            
            fail_count = 0
            with open(self.verification_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('username') == username and entry.get('status') == 'failed':
                            fail_count += 1
                    except json.JSONDecodeError:
                        continue
            
            return fail_count
        
        except Exception as e:
            print(f"⚠️ Error getting retry count: {e}")
            return 0
    
    def is_blacklisted(self, username: str) -> bool:
        """Cek apakah akun sudah blacklist (exceed max retries)"""
        try:
            if not self.blacklist_file.exists():
                return False
            
            with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                blacklist = json.load(f)
            
            if username in blacklist:
                return True
            
            # Alt check: hitung dari retry count
            return self.get_retry_count(username) >= self.max_retries
        
        except Exception as e:
            print(f"⚠️ Error checking blacklist: {e}")
            return False
    
    def blacklist_account(self, username: str, reason: str = "Verification failed max retries") -> bool:
        """Blacklist akun dari verification"""
        try:
            if not isinstance(username, str) or len(username) == 0:
                return False
            
            blacklist = {}
            if self.blacklist_file.exists():
                with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                    blacklist = json.load(f)
            
            blacklist[username] = {
                'blacklist_date': datetime.now().isoformat(),
                'reason': str(reason),
                'retry_count': self.get_retry_count(username)
            }
            
            with open(self.blacklist_file, 'w', encoding='utf-8') as f:
                json.dump(blacklist, f, indent=2, ensure_ascii=False)
            
            print(f"🚫 Akun {username} BLACKLIST: {reason}")
            self.log_verification_attempt(username, VerificationType.UNKNOWN, 'blacklist', 
                                         error_detail=reason)
            return True
        
        except Exception as e:
            print(f"❌ Error blacklisting account: {e}")
            return False
    
    def get_cooldown_remaining(self, username: str) -> Optional[timedelta]:
        """Get sisa waktu cooldown (jika ada)"""
        try:
            if not self.verification_log_file.exists():
                return None
            
            last_fail_time = None
            with open(self.verification_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('username') == username and entry.get('status') == 'failed':
                            last_fail_time = datetime.fromisoformat(entry.get('timestamp', ''))
                    except (json.JSONDecodeError, ValueError):
                        continue
            
            if last_fail_time:
                cooldown_end = last_fail_time + timedelta(minutes=self.cooldown_minutes)
                remaining = cooldown_end - datetime.now()
                if remaining.total_seconds() > 0:
                    return remaining
            
            return None
        
        except Exception as e:
            print(f"⚠️ Error calculating cooldown: {e}")
            return None
    
    def handle_verification_flow(self, username: str, verification_type: VerificationType,
                                  auto_code: Optional[str] = None,
                                  manual_code: Optional[str] = None) -> Tuple[bool, str]:
        """
        Handle verification dengan dual mode:
        - Auto: code dari parsing email/SMS
        - Manual: user input via Telegram
        """
        try:
            # Cek blacklist dulu
            if self.is_blacklisted(username):
                return False, f"🚫 BLACKLIST: Akun terlalu banyak verification fail (>{self.max_retries}x)"
            
            # Cek cooldown
            cooldown_remaining = self.get_cooldown_remaining(username)
            if cooldown_remaining:
                minutes_left = int(cooldown_remaining.total_seconds() / 60)
                return False, f"⏳ COOLDOWN: Coba lagi dalam {minutes_left} menit"
            
            # Mode 1: Auto code (dari OTP parsing nanti)
            if auto_code:
                result = self._verify_with_code(username, verification_type, auto_code)
                if result[0]:
                    self.log_verification_attempt(username, verification_type, 'success', auto_code)
                    print(f"✅ {username} verifikasi AUTO SUCCESS ({verification_type.value})")
                    return True, "✅ Verifikasi AUTO berhasil!"
                else:
                    self.log_verification_attempt(username, verification_type, 'failed', auto_code, result[1])
                    print(f"❌ {username} auto code FAILED: {result[1]}")
            
            # Mode 2: Manual code (tunggu user input via Telegram)
            if manual_code:
                result = self._verify_with_code(username, verification_type, manual_code)
                if result[0]:
                    self.log_verification_attempt(username, verification_type, 'success', manual_code)
                    print(f"✅ {username} verifikasi MANUAL SUCCESS ({verification_type.value})")
                    return True, "✅ Verifikasi MANUAL berhasil!"
                else:
                    self.log_verification_attempt(username, verification_type, 'failed', manual_code, result[1])
                    retry_count = self.get_retry_count(username)
                    if retry_count >= self.max_retries:
                        self.blacklist_account(username, f"Max retries reached ({retry_count}x)")
                        return False, f"🚫 Akun BLACKLIST: Terlalu banyak gagal ({retry_count}x)"
                    print(f"❌ {username} manual code FAILED: {result[1]} (attempt {retry_count}/{self.max_retries})")
                    return False, f"❌ Code invalid! Attempt {retry_count}/{self.max_retries}"
            
            # Jika tidak ada code, return pending
            self.log_verification_attempt(username, verification_type, 'pending')
            return False, f"⏳ PENDING: Tunggu input code ({verification_type.value})"
        
        except Exception as e:
            print(f"❌ Error handling verification: {e}")
            self.log_verification_attempt(username, verification_type, 'error', 
                                         error_detail=str(e))
            return False, f"❌ Error: {str(e)}"
    
    def _verify_with_code(self, username: str, verification_type: VerificationType,
                         code: str) -> Tuple[bool, str]:
        """
        Verify code validity (production version)
        TODO: integrate Instagram API verification nanti
        """
        try:
            # Validate code format
            if not code or not isinstance(code, str):
                return False, "Code tidak boleh kosong"
            
            code_clean = code.strip()
            
            # SMS: biasanya 6 digit
            if verification_type == VerificationType.SMS:
                if not code_clean.isdigit() or len(code_clean) < 4:
                    return False, "Code SMS harus numeric minimal 4 digit"
            
            # Email: bisa alphanumeric
            elif verification_type == VerificationType.EMAIL:
                if len(code_clean) < 4:
                    return False, "Code Email terlalu pendek"
            
            # 2FA: biasanya 6 digit dari authenticator
            elif verification_type == VerificationType.TWO_FA:
                if not code_clean.isdigit() or len(code_clean) != 6:
                    return False, "Code 2FA harus 6 digit"
            
            # Checkpoint: arbitrary format
            else:
                if len(code_clean) < 2:
                    return False, "Code terlalu pendek"
            
            # ✅ Code format valid
            return True, "Code format valid"
        
        except Exception as e:
            return False, f"Error validating code: {str(e)}"
    
    def get_verification_stats(self, username: str) -> Dict[str, Any]:
        """Get statistics verification akun"""
        try:
            stats = {
                'username': username,
                'total_attempts': 0,
                'success_count': 0,
                'failed_count': 0,
                'pending_count': 0,
                'is_blacklisted': self.is_blacklisted(username),
                'last_attempt': None
            }
            
            if not self.verification_log_file.exists():
                return stats
            
            with open(self.verification_log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get('username') == username:
                            stats['total_attempts'] += 1
                            status = entry.get('status', '')
                            if status == 'success':
                                stats['success_count'] += 1
                            elif status == 'failed':
                                stats['failed_count'] += 1
                            elif status == 'pending':
                                stats['pending_count'] += 1
                            
                            stats['last_attempt'] = entry.get('timestamp')
                    except json.JSONDecodeError:
                        continue
            
            return stats
        
        except Exception as e:
            print(f"⚠️ Error getting verification stats: {e}")
            return {}

def create_verification_handler():
    return VerificationHandler()
