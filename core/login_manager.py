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
    PleaseWaitFewMinutes,
    BadPassword,
    UserNotFound
)
from core.verification_handler import VerificationHandler

class LoginManager:
    def __init__(self):
        self.session_dir = "sessions"
        self.log_dir = "logs"
        self.accounts_file = "akun.json"
        self.current_client = None
        self.current_username = None
        
        os.makedirs(self.session_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
    
    def login(self, username: str, password: str) -> tuple[Client, bool]:
        """Login with session management"""
        client = Client()
        client.delay_range = [2, 5]
        
        session_file = os.path.join(self.session_dir, f"{username}.json")
        
        # Try loading existing session
        if os.path.exists(session_file):
            try:
                client.load_settings(session_file)
                client.login(username, password)
                
                # Verify session is valid
                client.get_timeline_feed()
                
                self.log_event("session_login", {"username": username})
                self.current_client = client
                self.current_username = username
                return client, True
                
            except Exception as e:
                self.log_event("session_expired", {
                    "username": username,
                    "error": str(e)
                })
                os.remove(session_file)
        
        # Fresh login
        try:
            client.login(username, password)
            client.dump_settings(session_file)
            
            self.log_event("fresh_login", {"username": username})
            self.current_client = client
            self.current_username = username
            return client, True
            
        except ChallengeRequired as e:
            self.log_event("challenge_required", {"username": username})
            handler = VerificationHandler(client, username)
            if handler.handle_challenge(e.challenge):
                self.current_client = client
                self.current_username = username
                return client, True
            return client, False
            
        except TwoFactorRequired:
            self.log_event("2fa_required", {"username": username})
            handler = VerificationHandler(client, username)
            if handler.handle_two_factor():
                self.current_client = client
                self.current_username = username
                return client, True
            return client, False
            
        except BadPassword:
            self.log_event("bad_password", {"username": username})
            print("❌ Password salah!")
            return client, False
            
        except UserNotFound:
            self.log_event("user_not_found", {"username": username})
            print("❌ Username tidak ditemukan!")
            return client, False
            
        except PleaseWaitFewMinutes as e:
            self.log_event("rate_limited", {"username": username})
            print(f"⏳ Rate limited! Tunggu beberapa menit...")
            return client, False
            
        except Exception as e:
            self.log_event("login_error", {
                "username": username,
                "error": str(e)
            })
            print(f"❌ Login error: {str(e)}")
            return client, False
    
    def logout(self):
        """Logout current session"""
        if self.current_client:
            try:
                self.current_client.logout()
                self.log_event("logout", {"username": self.current_username})
            except:
                pass
            self.current_client = None
            self.current_username = None
    
    def get_saved_accounts(self) -> list:
        """Get list of saved accounts"""
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, "r") as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def log_event(self, event_type: str, data: dict):
        """Log login events"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "data": data
        }
        
        log_file = os.path.join(self.log_dir, f"login_{datetime.now().strftime('%Y%m%d')}.log")
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"Log error: {e}")
