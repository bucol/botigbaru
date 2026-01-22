#!/usr/bin/env python3
"""
Login Manager - Enhanced & Integrated Version
Menerapkan "Device Consistency" dan "Indonesian Locale"
"""

import os
import time
import random
from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    TwoFactorRequired,
    PleaseWaitFewMinutes,
    BadPassword
)

# local imports
from core.session_manager_v2 import SessionManagerV2
from core.verification_handler import VerificationHandler
from core.account_manager import AccountManager
from core.device_identity_generator import DeviceIdentityGenerator  # INTEGRASI DISINI

load_dotenv()

class LoginManager:
    def __init__(self):
        self.session_manager = SessionManagerV2()
        self.verifier = VerificationHandler()
        self.account_manager = AccountManager()
        self.device_generator = DeviceIdentityGenerator() # Load generator
        self.max_retries = 3

    def _inject_device_settings(self, client: Client, username: str):
        """
        Menyuntikkan identitas HP palsu tapi konsisten ke Client.
        Agar Instagram mengira ini HP yang sama terus.
        """
        device_data = self.device_generator.get_identity(username)
        
        # Override settings instagrapi
        client.set_device({
            "app_version": device_data["app_version"],
            "android_version": device_data["android_version"],
            "android_release": device_data["android_release"],
            "dpi": device_data["dpi"],
            "resolution": device_data["display_resolution"],
            "manufacturer": device_data["manufacturer"],
            "device": device_data["device"],
            "model": device_data["model"],
            "cpu": device_data["cpu"],
            "version_code": "314665256" # Contoh build code valid
        })
        
        client.set_user_agent(
            f"Instagram {device_data['app_version']} Android ({device_data['android_release']}/{device_data['android_version']}; {device_data['dpi']}; {device_data['display_resolution']}; {device_data['manufacturer']}; {device_data['model']}; {device_data['device']}; {device_data['cpu']}; id_ID; 314665256)"
        )
        
        client.set_country(device_data['country'])
        client.set_locale(device_data['locale'])
        client.set_timezone_offset(device_data['timezone_offset'])
        
        # Inject UUIDs agar konsisten
        client.phone_id = device_data['phone_id']
        client.uuid = device_data['uuid']
        client.advertising_id = device_data['advertising_id']
        client.android_device_id = device_data['android_device_id']
        
        return client

    def login(self, username: str, password: str) -> Client | None:
        """
        Login satu akun dengan device settings yang konsisten
        """
        # 1. Setup Client dengan Device ID yang benar DULUAN
        client = Client()
        client = self._inject_device_settings(client, username)
        
        # 2. Coba Load Session (Cookie)
        try:
            if self.session_manager.load_session(client, username):
                print(f"✅ Session loaded untuk {username} (Device: {client.device_settings['model']})")
                # Validasi session
                try:
                    client.get_timeline_feed()
                    return client
                except LoginRequired:
                    print(f"⚠️ Session expired untuk {username}. Mencoba login ulang...")
        except Exception as e:
            print(f"ℹ️ Info: Belum ada session valid ({e})")

        # 3. Jika session mati/tidak ada, Login Manual (Username/Pass)
        for attempt in range(self.max_retries):
            try:
                print(f"🔑 Login attempt {attempt+1} untuk {username} via {client.device_settings['model']}...")
                
                # Tambah delay acak manusiawi sebelum hit server login
                time.sleep(random.uniform(2, 5)) 
                
                client.login(username, password)
                print(f"✅ Login sukses!")
                
                self.session_manager.save_session(client, username)
                return client

            except TwoFactorRequired:
                print(f"🔐 Masukkan Kode 2FA...")
                client = self.verifier.handle_two_factor(client, username, password)
                if client:
                    self.session_manager.save_session(client, username)
                    return client

            except ChallengeRequired:
                print(f"⚠️ Challenge Required...")
                client = self.verifier.handle_challenge(client, username)
                if client:
                    self.session_manager.save_session(client, username)
                    return client

            except PleaseWaitFewMinutes:
                print("⏳ Terkena limit 'Please Wait'. Tidur 3 menit...")
                time.sleep(180)
            
            except BadPassword:
                print("❌ Password salah! Berhenti mencoba.")
                return None

            except Exception as e:
                print(f"❌ Error login: {e}")
                time.sleep(5)

        return None

    def login_all_accounts(self):
        """Loop semua akun"""
        data = self.account_manager._load_accounts()
        if not data:
            print("📭 Tidak ada akun tersimpan.")
            return

        for acc in data:
            username = acc['username']
            password = acc['password']
            if self.login(username, password):
                print(f"🚀 {username} siap beraksi.\n")
            else:
                print(f"💀 {username} gagal diaktifkan.\n")

    def logout_account(self, username: str):
        self.session_manager.delete_session(username)
        print(f"🧹 Session {username} dihapus.")

if __name__ == "__main__":
    manager = LoginManager()
    manager.login_all_accounts()