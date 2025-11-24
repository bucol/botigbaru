#!/usr/bin/env python3
"""
Session Manager v2 - Auto clear session saat password berubah
Track session per akun + device identity injection
Production-grade dengan error handling & cross-platform safety
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

class SessionManagerV2:
    """Manage session + auto clear on password change (production-safe)"""
    
    def __init__(self):
        self.sessions_dir = Path('sessions/account_sessions')
        self.identities_dir = Path('sessions/account_identities')
        self.password_history_file = Path('data/password_history.json')
        self.session_log_file = Path('data/session_logs') / 'session_events.jsonl'
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create semua directory (safe cross-platform)"""
        try:
            self.sessions_dir.mkdir(parents=True, exist_ok=True)
            self.identities_dir.mkdir(parents=True, exist_ok=True)
            self.password_history_file.parent.mkdir(parents=True, exist_ok=True)
            self.session_log_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️ Warning creating directories: {e}")
    
    def _sanitize_username(self, username: str) -> str:
        """Escape special chars dari username untuk filename"""
        if not isinstance(username, str):
            raise ValueError("Username harus string")
        return "".join(c if c.isalnum() or c in '-_' else '_' for c in username)
    
    def create_session(self, username: str, device_identity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create session object dengan device identity injection
        Return: session object yang siap dipakai
        """
        try:
            if not isinstance(username, str) or len(username) == 0:
                raise ValueError("Username invalid")
            
            if not isinstance(device_identity, dict):
                raise ValueError("Device identity harus dict")
            
            session = {
                'username': username,
                'created_at': datetime.now().isoformat(),
                'device_identity': device_identity,
                'session_id': self._generate_session_id(),
                'status': 'active',
                'instagrapi_config': self._generate_instagrapi_config(device_identity)
            }
            
            self._log_session_event(username, 'session_created', session['session_id'])
            return session
        
        except Exception as e:
            print(f"❌ Error creating session: {e}")
            raise
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import random
        import string
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    def _generate_instagrapi_config(self, device_identity: Dict[str, Any]) -> Dict[str, Any]:
        """Generate config untuk instagrapi dengan device identity"""
        
        config = {
            'manufacturer': device_identity.get('manufacturer', 'Samsung'),
            'model': device_identity.get('model', 'SM-G991B'),
            'os_version': device_identity.get('android_version', 12),
            'device': device_identity.get('device', 'r0q'),
            'device_id': device_identity.get('device_id', ''),
            'android_id': device_identity.get('android_id', ''),
            'custom_headers': {
                'X-Device-ID': device_identity.get('device_id', ''),
                'X-Android-ID': device_identity.get('android_id', ''),
                'X-GSF-ID': device_identity.get('gsf_id', ''),
                'X-IMEI': device_identity.get('imei_1', ''),
                'X-MAC-Wifi': device_identity.get('mac_wifi', ''),
                'X-Build-Fingerprint': device_identity.get('fingerprint', ''),
                'X-Serial': device_identity.get('serial_number', ''),
            }
        }
        
        return config
    
    def inject_device_to_client(self, client: Any, device_identity: Dict[str, Any]) -> bool:
        """
        Inject device identity ke instagrapi Client
        Support: instagrapi v2.x dengan error handling
        """
        try:
            if client is None:
                raise ValueError("Client adalah None")
            
            # Method 1: set_device (standard instagrapi method)
            try:
                if hasattr(client, 'set_device'):
                    client.set_device(
                        manufacturer=device_identity.get('manufacturer', 'Samsung'),
                        model=device_identity.get('model', 'SM-G991B'),
                        os_version=device_identity.get('android_version', 12),
                        device=device_identity.get('device', 'r0q'),
                        device_id=device_identity.get('device_id', ''),
                    )
                    print(f"✅ Device injected via set_device()")
            except TypeError as e:
                # Fallback: parameter mungkin beda di versi lain
                print(f"⚠️ set_device() parameter error, trying alternative: {e}")
                if hasattr(client, 'set_device'):
                    client.set_device(
                        manufacturer=device_identity.get('manufacturer', 'Samsung'),
                        model=device_identity.get('model', 'SM-G991B'),
                    )
            
            # Method 2: Inject ke session object jika ada
            if hasattr(client, 'session'):
                client.session._device_identity = device_identity
            
            # Method 3: Store reference di client untuk audit nanti
            client._device_identity = device_identity
            
            self._log_session_event(device_identity.get('username', 'unknown'), 
                                   'device_injected', 
                                   device_identity.get('device_id', ''))
            return True
        
        except Exception as e:
            print(f"⚠️ Error injecting device: {e}")
            # Jangan raise, tetap return False tapi jangan crash
            return False
    
    def save_session(self, username: str, session: Dict[str, Any]) -> Tuple[bool, str]:
        """Save session file (safe)"""
        try:
            if not isinstance(username, str) or len(username) == 0:
                return False, "Username invalid"
            
            if not isinstance(session, dict):
                return False, "Session harus dict"
            
            safe_username = self._sanitize_username(username)
            session_file = self.sessions_dir / f"{safe_username}.json"
            
            # Backup existing session jika ada
            if session_file.exists():
                backup_file = self.sessions_dir / f"{safe_username}.backup.json"
                shutil.copy2(session_file, backup_file)
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session, f, indent=2, ensure_ascii=False)
            
            self._log_session_event(username, 'session_saved', session.get('session_id', ''))
            return True, str(session_file)
        
        except Exception as e:
            error_msg = f"Error saving session: {e}"
            print(f"❌ {error_msg}")
            self._log_session_event(username, 'session_save_failed', str(e))
            return False, error_msg
    
    def load_session(self, username: str) -> Optional[Dict[str, Any]]:
        """Load existing session (safe)"""
        try:
            if not isinstance(username, str) or len(username) == 0:
                return None
            
            safe_username = self._sanitize_username(username)
            session_file = self.sessions_dir / f"{safe_username}.json"
            
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    session = json.load(f)
                
                self._log_session_event(username, 'session_loaded', session.get('session_id', ''))
                return session
            
            return None
        
        except Exception as e:
            print(f"⚠️ Error loading session: {e}")
            self._log_session_event(username, 'session_load_failed', str(e))
            return None
    
    def clear_session(self, username: str) -> Tuple[bool, str]:
        """Delete session file (safe)"""
        try:
            if not isinstance(username, str) or len(username) == 0:
                return False, "Username invalid"
            
            safe_username = self._sanitize_username(username)
            session_file = self.sessions_dir / f"{safe_username}.json"
            
            if session_file.exists():
                session_file.unlink()
                self._log_session_event(username, 'session_cleared', '')
                print(f"✅ Session {username} cleared!")
                return True, "Session cleared"
            
            return False, "Session file tidak ditemukan"
        
        except Exception as e:
            error_msg = f"Error clearing session: {e}"
            print(f"⚠️ {error_msg}")
            self._log_session_event(username, 'session_clear_failed', str(e))
            return False, error_msg
    
    def on_password_changed(self, username: str) -> Dict[str, Any]:
        """
        AUTO-TRIGGER saat password diubah:
        1. Delete session file
        2. Delete identity file (force regenerate)
        3. Log password change
        4. Return status lengkap
        """
        try:
            if not isinstance(username, str) or len(username) == 0:
                raise ValueError("Username invalid")
            
            result = {
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'actions': [],
                'success': True,
                'errors': []
            }
            
            # Action 1: Clear session
            session_cleared, session_msg = self.clear_session(username)
            if session_cleared:
                result['actions'].append({
                    'action': 'session_cleared',
                    'status': 'success'
                })
            else:
                result['actions'].append({
                    'action': 'session_clear',
                    'status': 'warning',
                    'message': session_msg
                })
            
            # Action 2: Clear identity (force regenerate login berikutnya)
            safe_username = self._sanitize_username(username)
            identity_file = self.identities_dir / f"{safe_username}_identity.json"
            
            if identity_file.exists():
                try:
                    identity_file.unlink()
                    result['actions'].append({
                        'action': 'identity_cleared',
                        'status': 'success'
                    })
                except Exception as e:
                    result['actions'].append({
                        'action': 'identity_clear',
                        'status': 'error',
                        'message': str(e)
                    })
                    result['errors'].append(f"Identity clear failed: {e}")
            
            # Action 3: Log password change
            try:
                self._log_password_change(username)
                result['actions'].append({
                    'action': 'password_change_logged',
                    'status': 'success'
                })
            except Exception as e:
                result['actions'].append({
                    'action': 'password_change_log',
                    'status': 'error',
                    'message': str(e)
                })
                result['errors'].append(f"Password log failed: {e}")
            
            # Log event
            self._log_session_event(username, 'password_changed', json.dumps(result['actions']))
            
            print(f"🔄 Password change untuk {username}: {len(result['actions'])} actions")
            return result
        
        except Exception as e:
            print(f"❌ Error on_password_changed: {e}")
            return {
                'username': username,
                'timestamp': datetime.now().isoformat(),
                'success': False,
                'error': str(e)
            }
    
    def _log_password_change(self, username: str) -> bool:
        """Log setiap password change ke file history"""
        try:
            history = {}
            if self.password_history_file.exists():
                with open(self.password_history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            if username not in history:
                history[username] = []
            
            history[username].append({
                'changed_at': datetime.now().isoformat(),
                'session_cleared': True,
                'identity_cleared': True
            })
            
            with open(self.password_history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"⚠️ Error logging password change: {e}")
            return False
    
    def _log_session_event(self, username: str, event_type: str, event_data: str = ''):
        """Log session event ke JSONL (append-only)"""
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'username': username,
                'event_type': event_type,
                'event_data': event_data
            }
            
            with open(self.session_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
        
        except Exception as e:
            print(f"⚠️ Error logging session event: {e}")
    
    def get_password_change_history(self, username: str) -> list:
        """Get history password change akun"""
        try:
            if not self.password_history_file.exists():
                return []
            
            with open(self.password_history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            return history.get(username, [])
        
        except Exception as e:
            print(f"⚠️ Error getting password history: {e}")
            return []
    
    def get_session_stats(self, username: str) -> Dict[str, Any]:
        """Get statistik session akun"""
        try:
            session = self.load_session(username)
            history = self.get_password_change_history(username)
            
            stats = {
                'username': username,
                'session_exists': session is not None,
                'session_id': session.get('session_id', '') if session else None,
                'session_created': session.get('created_at', '') if session else None,
                'password_changes': len(history),
                'last_password_change': history[-1]['changed_at'] if history else None
            }
            
            return stats
        
        except Exception as e:
            print(f"⚠️ Error getting session stats: {e}")
            return {}
    
    def cleanup_old_backups(self, keep_days: int = 30):
        """Cleanup backup session files lama (opsional maintenance)"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            deleted_count = 0
            
            for backup_file in self.sessions_dir.glob('*.backup.json'):
                try:
                    file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_time < cutoff_date:
                        backup_file.unlink()
                        deleted_count += 1
                except Exception:
                    continue
            
            if deleted_count > 0:
                print(f"🧹 Cleaned up {deleted_count} old backup files")
            
            return deleted_count
        
        except Exception as e:
            print(f"⚠️ Error cleanup backups: {e}")
            return 0

def create_session_manager():
    return SessionManagerV2()
