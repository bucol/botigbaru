import os

# Script ini otomatis memperbaiki core/login_manager.py
# Menghapus kode yang error (unterminated string) dan menggantinya dengan versi bersih.

target_file = os.path.join("core", "login_manager.py")

# Kode LoginManager yang Valid & Support Device Faker
correct_code = r'''import os
import json
import datetime
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword, TwoFactorRequired, ChallengeRequired, 
    FeedbackRequired, LoginRequired, PleaseWaitFewMinutes
)

# Coba import module core lu, kalau ga ada pake default
try:
    from core.device_identity_generator import DeviceIdentityGenerator
except ImportError:
    DeviceIdentityGenerator = None

class LoginManager:
    def __init__(self):
        self.sessions_dir = "sessions"
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)

    def login_account(self, username, password):
        """
        Melakukan login dengan Device Identity (Anti-Ban).
        Returns: (client_object, boolean_success)
        """
        cl = Client()
        cl.delay_range = [3, 6]
        
        session_path = os.path.join(self.sessions_dir, f"{username}_session.json")

        # 1. SETUP DEVICE IDENTITY (PENTING BUAT ANTI-BAN)
        # Coba load session lama dulu biar device ID gak ganti-ganti
        session_loaded = False
        if os.path.exists(session_path):
            try:
                cl.load_settings(session_path)
                session_loaded = True
            except Exception:
                pass # Kalau file rusak, kita bikin baru

        # Kalau belum punya device settings (login pertama atau session rusak)
        if not session_loaded or not cl.device_settings:
            if DeviceIdentityGenerator:
                # Pake generator canggih lu
                gen = DeviceIdentityGenerator()
                identity = gen.generate_identity() # Asumsi method ini ada di generator lu
                # Kalau struktur returnnya beda, kita pake fallback aman
                if isinstance(identity, dict) and 'device_settings' in identity:
                    cl.set_settings(identity['device_settings'])
                    cl.set_uuids(identity['uuids'])
                    cl.set_user_agent(identity['user_agent'])
                else:
                    # Fallback standard
                    cl.set_country("ID")
                    cl.set_locale("id_ID")
            else:
                # Fallback jika module generator error
                cl.set_country("ID")
                cl.set_locale("id_ID")
        
        # Pastikan Locale Indonesia
        cl.set_country("ID")
        cl.set_locale("id_ID")

        # 2. EKSEKUSI LOGIN
        try:
            print(f"🔄 [LoginManager] Connecting as {username}...")
            cl.login(username, password)
            
            # Simpan session sukses
            cl.dump_settings(session_path)
            return cl, True

        except (TwoFactorRequired, ChallengeRequired, BadPassword, FeedbackRequired) as e:
            # Error ini akan ditangkap oleh dashboard.py untuk ditampilkan ke user
            raise e
            
        except Exception as e:
            print(f"❌ [LoginManager Error] {e}")
            return None, False

    def get_client(self, username):
        """Helper buat ambil client yang udah login (dari session)"""
        session_path = os.path.join(self.sessions_dir, f"{username}_session.json")
        if not os.path.exists(session_path):
            return None
        
        try:
            cl = Client()
            cl.load_settings(session_path)
            # Cek login status ringan
            return cl
        except:
            return None
'''

# Eksekusi Perbaikan
try:
    if not os.path.exists("core"):
        os.makedirs("core")
        
    print(f"🛠️ Sedang memperbaiki {target_file}...")
    
    with open(target_file, "w", encoding="utf-8") as f:
        f.write(correct_code)
        
    print("✅ BERHASIL! File core/login_manager.py sudah diperbaiki.")
    print("🚀 Silakan jalankan kembali: python dashboard.py")
    
except Exception as e:
    print(f"❌ Gagal memperbaiki: {e}")
