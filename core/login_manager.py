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
    LoginRequired, ChallengeRequired, TwoFactorRequired, 
    PleaseWaitFewMinutes, BadPassword
)

# local imports
from core.session_manager_v2 import SessionManagerV2
from core.verification_handler import VerificationHandler
from core.account_manager import AccountManager
from core.device_identity_generator import DeviceIdentityGenerator

load_dotenv()

class LoginManager:
    def __init__(self):
        self.session_manager = SessionManagerV2()
        self.verifier = VerificationHandler()
        self.account_manager = AccountManager()
        self.device_generator = DeviceIdentityGenerator()
        self.max_retries = 3

    # --- FIX: INI YANG TADI KURANG ---
    def get_accounts(self):
        """Wrapper untuk mengambil akun dari account_manager"""
        return self.account_manager.get_accounts()
    
    def logout(self, username):
        """Wrapper untuk logout"""
        return self.session_manager.delete_session(username)
    # ---------------------------------

    def _inject_device_settings(self, client: Client, username: str):
        device_data = self.device_generator.get_identity(username)
        
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
            "version_code": "314665256"
        })
        
        client.set_user_agent(
            f"Instagram {device_data['app_version']} Android ({device_data['android_release']}/{device_data['android_version']}; {device_data['dpi']}; {device_data['display_resolution']}; {device_data['manufacturer']}; {device_data['model']}; {device_data['device']}; {device_data['cpu']}; id_ID; 314665256)"
        )
        
        client.set_country(device_data['country'])
        client.set_locale(device_data['locale'])
        client.set_timezone_offset(device_data['timezone_offset'])
        
        client.phone_id = device_data['phone_id']
        client.uuid = device_data['uuid']
        client.advertising_id = device_data['advertising_id']
        client.android_device_id = device_data['android_device_id']
        
        return client

    def login(self, username: str, password: str) -> Client | None:
        client = Client()
        client = self._inject_device_settings(client, username)
        
        try:
            if self.session_manager.load_session(client, username):
                print(f"✅ Session loaded untuk {username}")
                try:
                    client.get_timeline_feed()
                    return client
                except LoginRequired:
                    print(f"⚠️ Session expired. Relogin...")
        except Exception as e:
            pass

        for attempt in range(self.max_retries):
            try:
                print(f"🔑 Login attempt {attempt+1} untuk {username}...")
                time.sleep(random.uniform(2, 5)) 
                client.login(username, password)
                print(f"✅ Login sukses!")
                self.session_manager.save_session(client, username)
                return client

            except TwoFactorRequired:
                client = self.verifier.handle_two_factor(client, username, password)
                if client:
                    self.session_manager.save_session(client, username)
                    return client
            except ChallengeRequired:
                client = self.verifier.handle_challenge(client, username)
                if client:
                    self.session_manager.save_session(client, username)
                    return client
            except Exception as e:
                print(f"❌ Error login: {e}")
                time.sleep(5)

        return None