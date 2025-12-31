import json
import os
import time
import random
import requests  # Tambahan untuk check proxy
import csv  # Tambahan untuk export CSV
from datetime import datetime
from typing import Tuple, Optional
import shutil  # Buat backup file

from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword, ReloginAttemptExceeded, ChallengeRequired,
    SelectContactPointRecoveryForm, RecaptchaChallengeForm,
    FeedbackRequired, LoginRequired
)

from core.device_identity_generator import DeviceIdentityGenerator
from core.session_manager import SessionManager

class LoginManager:
    def __init__(self):
        self.device_gen = DeviceIdentityGenerator()
        self.session_mgr = SessionManager()
        self.proxy_list = []  # List proxy untuk rotator (isi dari .env atau file)
        self._load_proxies()

    def _load_proxies(self):
        """Load proxy dari .env atau file proxies.txt"""
        proxies = os.getenv('PROXIES', '').split(',')
        if os.path.exists('proxies.txt'):
            with open('proxies.txt', 'r') as f:
                proxies.extend([line.strip() for line in f if line.strip()])
        self.proxy_list = [p for p in proxies if p]
        if self.proxy_list:
            print(f"Loaded {len(self.proxy_list)} proxies for rotator.")

    def _get_live_proxy(self):
        """Ambil proxy live random, check dengan requests"""
        if not self.proxy_list:
            return None
        random.shuffle(self.proxy_list)
        for proxy in self.proxy_list:
            try:
                requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=5)
                return proxy
            except:
                pass
        print("No live proxy found. Using direct connection.")
        return None

    def login_account(self, username: str, password: str) -> Tuple[Optional[Client], bool]:
        """Login dengan device faker, proxy rotator, dan challenge handler, plus auto backup"""
        client = Client()
        client.delay_range = [1, 3]  # Anti-ban delay

        # Set proxy rotator
        proxy = self._get_live_proxy()
        if proxy:
            client.set_proxy(proxy)
            print(f"Using proxy: {proxy}")

        # Generate device identity
        device = self.device_gen.generate_device_identity()
        client.set_device(device)

        # Coba load session dulu
        if self.session_mgr.load_session(client, username):
            try:
                client.get_timeline_feed()  # Verify session
                self._log_event(username, "Session loaded successfully")
                return client, True
            except LoginRequired:
                print("Session invalid, re-logging...")

        # Login manual jika session gagal
        try:
            client.login(username, password)
            self.session_mgr.save_session(client)
            self._backup_session(username)  # Auto backup setelah sukses
            self._log_event(username, "Login successful")
            return client, True

        except ChallengeRequired:
            return self._handle_challenge(client, username, password)

        except BadPassword:
            self._log_event(username, "Bad password")
            return None, False

        except ReloginAttemptExceeded:
            self._log_event(username, "Relogin attempt exceeded")
            return None, False

        except FeedbackRequired:
            self._log_event(username, "Feedback required")
            return None, False

        except Exception as e:
            self._log_event(username, f"Login error: {str(e)}")
            return None, False

    def _handle_challenge(self, client: Client, username: str, password: str) -> Tuple[Optional[Client], bool]:
        """Handle challenge dengan rotator proxy jika gagal"""
        print("\n[CHALLENGE] Akun memerlukan verifikasi!")
        try:
            api_path = client.last_json.get("challenge", {}).get("api_path")
            if not api_path:
                return None, False

            choices = client.challenge_code_handler(username, lambda: print("Pilih metode: 0=SMS, 1=Email"))
            choice = input("Pilih metode (0/1): ")

            client.challenge_code_handler(username, choice)
            code = input("Masukkan kode verifikasi: ")

            client.challenge_code_handler(username, code)

            client.login(username, password)
            self.session_mgr.save_session(client)
            self._backup_session(username)  # Auto backup
            self._log_event(username, "Challenge resolved")
            return client, True

        except SelectContactPointRecoveryForm:
            print("[CHALLENGE] Select contact point")
            # Logic serupa, rotator proxy jika gagal
            proxy = self._get_live_proxy()
            if proxy:
                client.set_proxy(proxy)
            # ... (lanjutkan logic handle)

        except RecaptchaChallengeForm:
            print("[CHALLENGE] Recaptcha required. Silakan login manual dulu.")
            return None, False

        except Exception as e:
            self._log_event(username, f"Challenge error: {str(e)}")
            return None, False

    def _log_event(self, username: str, message: str):
        """Log event ke file"""
        log_entry = {
            "timestamp": str(datetime.now()),
            "username": username,
            "event": message
        }
        log_file = "login_logs.json"
        if os.path.exists(log_file):
            with open(log_file, 'r+') as f:
                logs = json.load(f)
                logs.append(log_entry)
                f.seek(0)
                json.dump(logs, f, indent=2)
        else:
            with open(log_file, 'w') as f:
                json.dump([log_entry], f, indent=2)

    def export_logs_to_csv(self, csv_file="login_logs.csv"):
        """Export logs JSON ke CSV"""
        log_file = "login_logs.json"
        if not os.path.exists(log_file):
            print("No logs to export!")
            return
        with open(log_file, 'r') as f:
            logs = json.load(f)
        with open(csv_file, 'w', newline='') as cf:
            writer = csv.writer(cf)
            writer.writerow(['timestamp', 'username', 'event'])  # Header
            for log in logs:
                writer.writerow([log['timestamp'], log['username'], log['event']])
        print(f"Logs exported to {csv_file}")

    def _backup_session(self, username: str):
        """Fitur baru: Backup session otomatis ke folder backups/ dengan timestamp"""
        session_file = f"sessions/{username}.json"  # Asumsi dari session_manager
        if os.path.exists(session_file):
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            backup_file = os.path.join(backup_dir, f"{username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            shutil.copy(session_file, backup_file)
            print(f"Session backed up to {backup_file}")

    def restore_session(self, username: str, backup_file: str):
        """Fitur baru: Restore session dari backup"""
        session_file = f"sessions/{username}.json"
        if os.path.exists(backup_file):
            shutil.copy(backup_file, session_file)
            print(f"Session restored from {backup_file}")
        else:
            print("Backup file not found!")