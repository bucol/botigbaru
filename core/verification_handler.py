import json
import os
import time
import random
from datetime import datetime
from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    TwoFactorRequired,
    LoginRequired,
    PleaseWaitFewMinutes
)

class VerificationHandler:
    def __init__(self, client: Client, username: str):
        self.client = client
        self.username = username
        self.session_dir = "sessions"
        self.log_dir = "logs"
        self.max_retries = 3
        self.challenge_methods = ['email', 'sms']
        
        os.makedirs(self.session_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
    
    def handle_challenge(self, challenge_info: dict) -> bool:
        """Handle Instagram challenge/verification"""
        try:
            self.log_event("challenge_detected", {
                "type": challenge_info.get('step_name', 'unknown'),
                "message": challenge_info.get('message', '')
            })
            
            step_name = challenge_info.get('step_name', '')
            
            if 'verify_email' in step_name or 'email' in step_name.lower():
                return self._handle_email_verification()
            elif 'verify_sms' in step_name or 'sms' in step_name.lower():
                return self._handle_sms_verification()
            elif 'select_verify_method' in step_name:
                return self._handle_method_selection(challenge_info)
            else:
                self.log_event("unknown_challenge", {"step": step_name})
                return False
                
        except Exception as e:
            self.log_event("challenge_error", {"error": str(e)})
            return False
    
    def _handle_method_selection(self, challenge_info: dict) -> bool:
        """Let user select verification method"""
        print("\n" + "="*50)
        print("🔐 VERIFIKASI DIPERLUKAN")
        print("="*50)
        print("Pilih metode verifikasi:")
        print("1. Email")
        print("2. SMS")
        print("0. Batal")
        
        choice = input("\nPilihan [1/2/0]: ").strip()
        
        if choice == "1":
            self.client.challenge_code_handler = self._email_code_handler
            return self._handle_email_verification()
        elif choice == "2":
            self.client.challenge_code_handler = self._sms_code_handler
            return self._handle_sms_verification()
        else:
            return False
    
    def _handle_email_verification(self) -> bool:
        """Handle email verification"""
        print("\n📧 Kode verifikasi dikirim ke EMAIL")
        return self._process_verification_code("email")
    
    def _handle_sms_verification(self) -> bool:
        """Handle SMS verification"""
        print("\n📱 Kode verifikasi dikirim ke SMS")
        return self._process_verification_code("sms")
    
    def _process_verification_code(self, method: str) -> bool:
        """Process verification code input"""
        for attempt in range(self.max_retries):
            print(f"\nPercobaan {attempt + 1}/{self.max_retries}")
            code = input(f"Masukkan kode verifikasi ({method}): ").strip()
            
            if not code:
                print("❌ Kode tidak boleh kosong!")
                continue
            
            if not code.isdigit() or len(code) != 6:
                print("❌ Kode harus 6 digit angka!")
                continue
            
            try:
                result = self.client.challenge_resolve(code)
                if result:
                    self.log_event("verification_success", {"method": method})
                    print("✅ Verifikasi berhasil!")
                    self._save_session()
                    return True
                else:
                    print("❌ Kode salah, coba lagi...")
                    
            except Exception as e:
                self.log_event("verification_failed", {
                    "method": method,
                    "attempt": attempt + 1,
                    "error": str(e)
                })
                print(f"❌ Error: {str(e)}")
        
        print("❌ Verifikasi gagal setelah 3 percobaan")
        return False
    
    def _email_code_handler(self, username: str, choice: str) -> str:
        """Handler for email verification code"""
        code = input("📧 Masukkan kode dari EMAIL: ").strip()
        return code
    
    def _sms_code_handler(self, username: str, choice: str) -> str:
        """Handler for SMS verification code"""
        code = input("📱 Masukkan kode dari SMS: ").strip()
        return code
    
    def handle_two_factor(self) -> bool:
        """Handle 2FA authentication"""
        print("\n" + "="*50)
        print("🔐 TWO-FACTOR AUTHENTICATION")
        print("="*50)
        
        for attempt in range(self.max_retries):
            code = input("Masukkan kode 2FA: ").strip()
            
            if not code:
                continue
                
            try:
                result = self.client.two_factor_login(code)
                if result:
                    self.log_event("2fa_success", {})
                    print("✅ 2FA berhasil!")
                    self._save_session()
                    return True
            except Exception as e:
                self.log_event("2fa_failed", {"error": str(e)})
                print(f"❌ Error: {str(e)}")
        
        return False
    
    def _save_session(self):
        """Save session after successful verification"""
        try:
            session_file = os.path.join(self.session_dir, f"{self.username}.json")
            self.client.dump_settings(session_file)
            self.log_event("session_saved", {"file": session_file})
        except Exception as e:
            self.log_event("session_save_error", {"error": str(e)})
    
    def log_event(self, event_type: str, data: dict):
        """Log verification events"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": self.username,
            "event": event_type,
            "data": data
        }
        
        log_file = os.path.join(self.log_dir, f"verification_{datetime.now().strftime('%Y%m%d')}.log")
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Log error: {e}")
    
    def wait_with_message(self, seconds: int, message: str = "Menunggu"):
        """Wait with countdown display"""
        for i in range(seconds, 0, -1):
            print(f"\r{message}: {i} detik...", end="", flush=True)
            time.sleep(1)
        print()
