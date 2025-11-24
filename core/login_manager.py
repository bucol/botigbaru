#!/usr/bin/env python3
"""
Login Manager - Instagrapi Client Integration
Handle: login flow, device injection, verification, session persistence
Production-grade dengan error recovery & anti-ban measures
"""

import time
import json
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, BadPassword, InvalidUser, 
    CheckpointRequired, ChallengeRequired, TwoFactorRequired
)

from core.account_manager import AccountManager

class LoginManager:
    """
    Manage login flow dengan instagrapi Client
    Handle: device injection, verification, error recovery
    """
    
    def __init__(self):
        self.account_manager = AccountManager()
        self.active_clients = {}  # username -> client mapping
        self.login_log_file = Path('logs/login_operations') / f'{datetime.now().strftime("%Y-%m-%d")}.jsonl'
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create log directories"""
        try:
            Path('logs/login_operations').mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️ Warning: {e}")
    
    def _log_login_event(self, username: str, event_type: str, status: str, details: Dict[str, Any] = None):
        """Log login event ke JSONL"""
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'event_type': event_type,
                'status': status,
                'details': details or {}
            }
            
            self.login_log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.login_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        except Exception as e:
            print(f"⚠️ Error logging login event: {e}")
    
    def create_client(self, use_proxy: bool = False, proxy_url: str = None) -> Client:
        """
        Create fresh instagrapi Client instance
        Optional: dengan proxy support
        """
        try:
            client = Client()
            
            # Set proxy jika ada
            if use_proxy and proxy_url:
                try:
                    client.set_proxy(proxy_url)
                    print(f"✅ Proxy set: {proxy_url}")
                except Exception as e:
                    print(f"⚠️ Error setting proxy: {e}")
            
            return client
        
        except Exception as e:
            print(f"❌ Error creating client: {e}")
            return None
    
    def login(self, username: str, password: str, use_proxy: bool = False, 
              proxy_url: str = None) -> Tuple[bool, str, Optional[Client]]:
        """
        Complete login flow:
        1. Check account exist
        2. Create instagrapi client
        3. Inject device identity
        4. Attempt login
        5. Handle verification/errors
        6. Persist session
        """
        try:
            if not isinstance(username, str) or not isinstance(password, str):
                return False, "Username/password invalid", None
            
            print(f"\n🔐 Starting login for @{username}...")
            self._log_login_event(username, 'login_start', 'initiated')
            
            # Step 1: Register atau load existing account
            account_exists = username in self.account_manager.accounts_db
            
            if not account_exists:
                print(f"📝 Account tidak ditemukan, registering baru...")
                reg_success, reg_msg, reg_data = self.account_manager.register_account(
                    username, self._hash_password(password), email=None
                )
                if not reg_success:
                    self._log_login_event(username, 'account_registration', 'failed', {'error': reg_msg})
                    return False, f"Registration failed: {reg_msg}", None
                
                device_identity = reg_data['device_identity']
            else:
                print(f"✅ Account found, loading existing...")
                device_identity = self.account_manager.identity_gen.load_identity(username)
                if not device_identity:
                    device_identity = self.account_manager.identity_gen.get_or_create_identity(username)
            
            # Step 2: Create instagrapi client
            print(f"🔧 Creating instagrapi client...")
            client = self.create_client(use_proxy=use_proxy, proxy_url=proxy_url)
            
            if not client:
                self._log_login_event(username, 'client_creation', 'failed')
                return False, "Failed to create client", None
            
            # Step 3: Inject device identity
            print(f"📱 Injecting device identity: {device_identity.get('model')}...")
            inject_success = self.account_manager.session_manager.inject_device_to_client(
                client, device_identity
            )
            
            if not inject_success:
                print(f"⚠️ Device injection warning, proceeding...")
            
            self._log_login_event(username, 'device_injected', 'success', {
                'device_model': device_identity.get('model'),
                'device_id': device_identity.get('device_id')
            })
            
            # Step 4: Attempt login
            print(f"🔑 Attempting login...")
            login_success, login_msg = self._attempt_login(
                client, username, password, device_identity
            )
            
            if not login_success:
                # Check jika verification/checkpoint required
                verification_msg = self._handle_login_error(
                    client, username, login_msg, device_identity
                )
                
                self._log_login_event(username, 'login_attempt', 'verification_required', {
                    'error': login_msg,
                    'verification_needed': True
                })
                
                print(f"⚠️ Login verification required: {verification_msg}")
                return False, verification_msg, client
            
            # Step 5: Login success
            print(f"✅ Login successful!")
            
            # Store client reference
            self.active_clients[username] = client
            
            # Update account metadata
            login_ok, _, _ = self.account_manager.login_account(
                username, self._hash_password(password), client=client
            )
            
            self._log_login_event(username, 'login_success', 'success', {
                'device_model': device_identity.get('model'),
                'user_id': self._get_user_id(client)
            })
            
            return True, "Login successful", client
        
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            self._log_login_event(username, 'login_error', 'failed', {'error': str(e)})
            return False, error_msg, None
    
    def _attempt_login(self, client: Client, username: str, password: str, 
                      device_identity: Dict[str, Any]) -> Tuple[bool, str]:
        """Attempt login ke Instagram dengan error handling"""
        try:
            print(f"   Sending login request...")
            client.login(username, password)
            
            print(f"   ✅ Authentication successful")
            return True, "Login success"
        
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
            error_str = str(e).lower()
            
            if 'checkpoint' in error_str or 'unusual activity' in error_str:
                return False, "CHECKPOINT: Unusual activity detected"
            elif 'challenge' in error_str:
                return False, "CHALLENGE: Security challenge required"
            elif 'rate limit' in error_str or 'too many' in error_str:
                return False, "RATE_LIMIT: Too many login attempts"
            elif 'sms' in error_str or 'phone' in error_str:
                return False, "SMS_VERIFICATION: SMS verification needed"
            elif 'email' in error_str:
                return False, "EMAIL_VERIFICATION: Email verification needed"
            elif 'disabled' in error_str or 'banned' in error_str:
                return False, "ACCOUNT_DISABLED: Account disabled/banned"
            else:
                return False, f"LOGIN_ERROR: {str(e)}"
    
    def _handle_login_error(self, client: Client, username: str, error_msg: str, 
                           device_identity: Dict[str, Any]) -> str:
        """
        Handle login errors dan verification requirements
        Return: user-friendly message + next action
        """
        try:
            # Deteksi error type
            is_verif, verif_type = self.account_manager.verification_handler.detect_verification_required(error_msg)
            
            if not is_verif:
                return error_msg
            
            # Log verification pending
            self.account_manager.verification_handler.log_verification_attempt(
                username, verif_type, 'pending'
            )
            
            # Return helpful message
            if verif_type.value == 'sms':
                return f"📱 SMS verification required\n✉️ Cek SMS yang dikirim ke nomor terdaftar\n⏳ Tunggu code atau input manual via menu"
            
            elif verif_type.value == 'email':
                return f"📧 Email verification required\n✉️ Cek email yang dikirim\n⏳ Tunggu code atau input manual via menu"
            
            elif verif_type.value == 'checkpoint':
                return f"🔒 Checkpoint verification required\n⚠️ Instagram mendeteksi aktivitas mencurigakan\n⏳ Tunggu atau confirm via Instagram app"
            
            elif verif_type.value == '2fa':
                return f"🔐 2FA verification required\n📱 Buka authenticator app\n⏳ Input 6-digit code saat diminta"
            
            elif verif_type.value == 'security_alert':
                return f"🚨 Security alert\n⚠️ Activity terdeteksi dari lokasi/device baru\n⏳ Confirm di Instagram app atau email"
            
            else:
                return f"✋ Verification needed: {verif_type.value}\n⏳ Follow Instagram instructions"
        
        except Exception as e:
            print(f"⚠️ Error handling error: {e}")
            return error_msg
    
    def verify_code(self, username: str, code: str) -> Tuple[bool, str]:
        """
        Verify code yang user provide
        (Integration ke verification handler)
        """
        try:
            if username not in self.account_manager.accounts_db:
                return False, "Account tidak ditemukan"
            
            # Get verification type yang pending
            verif_stats = self.account_manager.verification_handler.get_verification_stats(username)
            
            if verif_stats['pending_count'] == 0:
                return False, "Tidak ada pending verification"
            
            # Handle verification dengan manual code
            verif_success, verif_msg = self.account_manager.handle_login_verification(
                username, 
                verification_error="manual_code_input",
                manual_code=code
            )
            
            self._log_login_event(username, 'verification_code_submit', 
                                 'success' if verif_success else 'failed',
                                 {'code_valid': verif_success})
            
            return verif_success, verif_msg
        
        except Exception as e:
            error_msg = f"Error verifying code: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def logout(self, username: str) -> Tuple[bool, str]:
        """Logout akun"""
        try:
            if username not in self.active_clients:
                return False, "Client tidak aktif"
            
            client = self.active_clients[username]
            
            # Clear session
            self.account_manager.session_manager.clear_session(username)
            
            # Remove client reference
            del self.active_clients[username]
            
            self._log_login_event(username, 'logout', 'success')
            
            print(f"✅ Logged out: @{username}")
            return True, "Logout successful"
        
        except Exception as e:
            error_msg = f"Error logging out: {str(e)}"
            print(f"❌ {error_msg}")
            self._log_login_event(username, 'logout_error', 'failed', {'error': str(e)})
            return False, error_msg
    
    def get_client(self, username: str) -> Optional[Client]:
        """Get active client untuk username"""
        return self.active_clients.get(username)
    
    def is_logged_in(self, username: str) -> bool:
        """Check apakah username currently logged in"""
        return username in self.active_clients
    
    def get_logged_in_accounts(self) -> list:
        """Get list akun yang currently logged in"""
        return list(self.active_clients.keys())
    
    def _hash_password(self, password: str) -> str:
        """
        Simple password hashing (production: gunakan bcrypt/argon2)
        Untuk demo, use sha256
        """
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _get_user_id(self, client: Client) -> Optional[str]:
        """Get Instagram user ID dari client"""
        try:
            if hasattr(client, 'user_id'):
                return str(client.user_id)
            elif hasattr(client, 'account_id'):
                return str(client.account_id)
        except:
            pass
        
        return None
    
    def get_login_statistics(self) -> Dict[str, Any]:
        """Get login statistics"""
        try:
            stats = {
                'total_active_sessions': len(self.active_clients),
                'logged_in_accounts': self.get_logged_in_accounts(),
                'account_manager_stats': self.account_manager.get_statistics()
            }
            
            return stats
        
        except Exception as e:
            print(f"⚠️ Error getting stats: {e}")
            return {}

def create_login_manager():
    return LoginManager()
