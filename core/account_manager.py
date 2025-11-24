#!/usr/bin/env python3
"""
Account Manager - Integration Module
Gabung: Device Identity + Verification + Session Management
Production-grade account lifecycle management
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from core.device_identity_generator import DeviceIdentityGenerator
from core.verification_handler import VerificationHandler, VerificationType
from core.session_manager_v2 import SessionManagerV2

class AccountManager:
    """
    Master manager untuk seluruh akun lifecycle:
    - Generate identity unik per akun
    - Handle verification
    - Manage session dengan device injection
    - Auto clear on password change
    - Audit & logging
    """
    
    def __init__(self):
        self.identity_gen = DeviceIdentityGenerator()
        self.verification_handler = VerificationHandler(max_retries=5, cooldown_minutes=30)
        self.session_manager = SessionManagerV2()
        self.accounts_db_file = Path('data/accounts_db.json')
        self.accounts_db = self._load_accounts_db()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create semua directory"""
        try:
            Path('data').mkdir(parents=True, exist_ok=True)
            Path('sessions/account_sessions').mkdir(parents=True, exist_ok=True)
            Path('sessions/account_identities').mkdir(parents=True, exist_ok=True)
            Path('data/verification_logs').mkdir(parents=True, exist_ok=True)
            Path('data/session_logs').mkdir(parents=True, exist_ok=True)
            Path('logs/account_operations').mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️ Warning creating directories: {e}")
    
    def _load_accounts_db(self) -> Dict[str, Any]:
        """Load database akun yang sudah terdaftar"""
        try:
            if self.accounts_db_file.exists():
                with open(self.accounts_db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading accounts DB: {e}")
        
        return {}
    
    def _save_accounts_db(self):
        """Save accounts database"""
        try:
            with open(self.accounts_db_file, 'w', encoding='utf-8') as f:
                json.dump(self.accounts_db, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Error saving accounts DB: {e}")
    
    def _log_operation(self, operation_type: str, username: str, status: str, details: Dict[str, Any] = None):
        """Log setiap operasi akun ke file terpisah"""
        try:
            log_file = Path('logs/account_operations') / f'{datetime.now().strftime("%Y-%m-%d")}.jsonl'
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation_type,
                'username': username,
                'status': status,
                'details': details or {}
            }
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        
        except Exception as e:
            print(f"⚠️ Error logging operation: {e}")
    
    def register_account(self, username: str, password_hash: str, email: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Register akun baru dengan:
        1. Generate device identity unik (completely random)
        2. Store ke database
        3. Create session
        """
        try:
            if not isinstance(username, str) or len(username) == 0:
                return False, "Username invalid", {}
            
            # Cek duplicate
            if username in self.accounts_db:
                return False, f"Akun {username} sudah terdaftar", {}
            
            # Generate device identity
            device_identity = self.identity_gen.get_or_create_identity(username)
            
            # Create session object
            session = self.session_manager.create_session(username, device_identity)
            
            # Store account metadata
            account_data = {
                'username': username,
                'password_hash': password_hash,
                'email': email,
                'registered_at': datetime.now().isoformat(),
                'device_id': device_identity.get('device_id'),
                'device_model': device_identity.get('model'),
                'status': 'active',
                'session_id': session['session_id'],
                'verification_status': 'pending',
                'last_login': None
            }
            
            self.accounts_db[username] = account_data
            self._save_accounts_db()
            
            # Log operation
            self._log_operation('account_registered', username, 'success', {
                'device_model': device_identity.get('model'),
                'device_id': device_identity.get('device_id')
            })
            
            result = {
                'username': username,
                'device_identity': device_identity,
                'session': session
            }
            
            print(f"✅ Account registered: {username} | Device: {device_identity.get('model')}")
            return True, "Account registered successfully", result
        
        except Exception as e:
            error_msg = f"Error registering account: {str(e)}"
            print(f"❌ {error_msg}")
            self._log_operation('account_register_failed', username, 'failed', {'error': str(e)})
            return False, error_msg, {}
    
    def login_account(self, username: str, password_hash: str, client=None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Login akun dengan:
        1. Load device identity
        2. Inject ke instagrapi client
        3. Handle verification jika needed
        4. Create session
        """
        try:
            if not isinstance(username, str) or len(username) == 0:
                return False, "Username invalid", {}
            
            # Cek akun exist
            if username not in self.accounts_db:
                return False, f"Akun {username} tidak ditemukan", {}
            
            account_data = self.accounts_db[username]
            
            # Load device identity
            device_identity = self.identity_gen.load_identity(username)
            if not device_identity:
                # Jika identity hilang (misal: password change), generate baru
                device_identity = self.identity_gen.get_or_create_identity(username)
            
            # Create session
            session = self.session_manager.create_session(username, device_identity)
            
            # Inject device ke client (jika provided)
            if client:
                self.session_manager.inject_device_to_client(client, device_identity)
            
            # Update last login
            account_data['last_login'] = datetime.now().isoformat()
            account_data['session_id'] = session['session_id']
            self._save_accounts_db()
            
            # Save session file
            session_saved, session_path = self.session_manager.save_session(username, session)
            
            self._log_operation('account_login', username, 'success', {
                'device_model': device_identity.get('model'),
                'session_id': session['session_id']
            })
            
            result = {
                'username': username,
                'device_identity': device_identity,
                'session': session,
                'session_saved': session_saved
            }
            
            print(f"✅ Account logged in: {username} | Device: {device_identity.get('model')}")
            return True, "Login successful", result
        
        except Exception as e:
            error_msg = f"Error login account: {str(e)}"
            print(f"❌ {error_msg}")
            self._log_operation('account_login_failed', username, 'failed', {'error': str(e)})
            return False, error_msg, {}
    
    def handle_login_verification(self, username: str, verification_error: str, 
                                  auto_code: str = None, manual_code: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Handle verification saat login:
        1. Deteksi tipe verification
        2. Cek blacklist/cooldown
        3. Verify dengan code (auto atau manual)
        4. Update status
        """
        try:
            if not isinstance(username, str) or len(username) == 0:
                return False, "Username invalid", {}
            
            if username not in self.accounts_db:
                return False, f"Akun {username} tidak ditemukan", {}
            
            # Deteksi verification type
            is_verification, verif_type = self.verification_handler.detect_verification_required(verification_error)
            
            if not is_verification:
                return False, "Verification tidak terdeteksi", {}
            
            # Handle verification flow
            verif_success, verif_msg = self.verification_handler.handle_verification_flow(
                username, verif_type, auto_code=auto_code, manual_code=manual_code
            )
            
            if verif_success:
                # Update account status
                self.accounts_db[username]['verification_status'] = 'verified'
                self._save_accounts_db()
                
                self._log_operation('verification_success', username, 'success', {
                    'verification_type': verif_type.value,
                    'code_provided': bool(auto_code or manual_code)
                })
                
                result = {
                    'username': username,
                    'verification_type': verif_type.value,
                    'status': 'verified'
                }
                
                print(f"✅ Verification success: {username} | Type: {verif_type.value}")
                return True, verif_msg, result
            
            else:
                # Check jika blacklist
                if self.verification_handler.is_blacklisted(username):
                    self.accounts_db[username]['status'] = 'blacklisted'
                    self._save_accounts_db()
                    self._log_operation('account_blacklisted', username, 'failed', {
                        'reason': 'verification_max_retries'
                    })
                
                self._log_operation('verification_failed', username, 'failed', {
                    'verification_type': verif_type.value,
                    'message': verif_msg
                })
                
                print(f"❌ Verification failed: {username} | {verif_msg}")
                return False, verif_msg, {}
        
        except Exception as e:
            error_msg = f"Error handling verification: {str(e)}"
            print(f"❌ {error_msg}")
            self._log_operation('verification_error', username, 'error', {'error': str(e)})
            return False, error_msg, {}
    
    def change_password(self, username: str, new_password_hash: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Change password akun:
        1. Auto clear session
        2. Auto clear identity (force regenerate)
        3. Update password
        4. Log operation
        """
        try:
            if not isinstance(username, str) or len(username) == 0:
                return False, "Username invalid", {}
            
            if username not in self.accounts_db:
                return False, f"Akun {username} tidak ditemukan", {}
            
            # Trigger password change flow
            change_result = self.session_manager.on_password_changed(username)
            
            # Update password di database
            self.accounts_db[username]['password_hash'] = new_password_hash
            self.accounts_db[username]['password_changed_at'] = datetime.now().isoformat()
            self.accounts_db[username]['verification_status'] = 'pending'  # Reset verification
            self._save_accounts_db()
            
            self._log_operation('password_changed', username, 'success', {
                'session_cleared': True,
                'identity_cleared': True,
                'actions': change_result.get('actions', [])
            })
            
            result = {
                'username': username,
                'password_changed': True,
                'session_cleared': True,
                'identity_regenerate': True,
                'change_details': change_result
            }
            
            print(f"✅ Password changed: {username} | Session & Identity cleared")
            return True, "Password changed successfully", result
        
        except Exception as e:
            error_msg = f"Error changing password: {str(e)}"
            print(f"❌ {error_msg}")
            self._log_operation('password_change_failed', username, 'failed', {'error': str(e)})
            return False, error_msg, {}
    
    def get_account_info(self, username: str) -> Dict[str, Any]:
        """Get info lengkap akun"""
        try:
            if username not in self.accounts_db:
                return {}
            
            account = self.accounts_db[username].copy()
            device_identity = self.identity_gen.load_identity(username)
            session = self.session_manager.load_session(username)
            verif_stats = self.verification_handler.get_verification_stats(username)
            
            account['device_identity_summary'] = {
                'model': device_identity.get('model') if device_identity else None,
                'device_id': device_identity.get('device_id') if device_identity else None,
                'android_version': device_identity.get('android_version') if device_identity else None
            } if device_identity else None
            
            account['session_summary'] = {
                'session_id': session.get('session_id') if session else None,
                'created_at': session.get('created_at') if session else None
            } if session else None
            
            account['verification_stats'] = verif_stats
            
            return account
        
        except Exception as e:
            print(f"⚠️ Error getting account info: {e}")
            return {}
    
    def list_all_accounts(self) -> list:
        """List semua akun (summary)"""
        try:
            result = []
            for username, account_data in self.accounts_db.items():
                result.append({
                    'username': username,
                    'status': account_data.get('status', 'unknown'),
                    'device_model': account_data.get('device_model', 'N/A'),
                    'registered_at': account_data.get('registered_at', 'N/A'),
                    'last_login': account_data.get('last_login', 'Never'),
                    'verification_status': account_data.get('verification_status', 'unknown')
                })
            
            return result
        
        except Exception as e:
            print(f"⚠️ Error listing accounts: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistik global"""
        try:
            stats = {
                'total_accounts': len(self.accounts_db),
                'active_accounts': len([a for a in self.accounts_db.values() if a.get('status') == 'active']),
                'blacklisted_accounts': len([a for a in self.accounts_db.values() if a.get('status') == 'blacklisted']),
                'verified_accounts': len([a for a in self.accounts_db.values() if a.get('verification_status') == 'verified']),
                'pending_verification': len([a for a in self.accounts_db.values() if a.get('verification_status') == 'pending']),
                'timestamp': datetime.now().isoformat()
            }
            
            return stats
        
        except Exception as e:
            print(f"⚠️ Error getting statistics: {e}")
            return {}

def create_account_manager():
    return AccountManager()
