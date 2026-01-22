#!/usr/bin/env python3
"""
Device Identity Generator - Enhanced Version
Generate and PERSIST realistic Android device identities.
Memastikan satu akun selalu menggunakan HP yang sama (Anti-Suspicious Login).
"""

import json
import random
import uuid
import hashlib
import os
from datetime import datetime

class DeviceIdentityGenerator:
    def __init__(self):
        # Database HP yang lebih lengkap dengan resolusi layar & DPI yang akurat
        # Format: (Brand, Model, DeviceName, Width, Height, DPI, Android Ver)
        self.devices_db = [
            ("Samsung", "SM-G991B", "r0q", 1080, 2400, 480, 31),      # S21
            ("Samsung", "SM-A525F", "a52q", 1080, 2400, 420, 30),     # A52
            ("Xiaomi", "M2102J20SG", "vayu", 1080, 2400, 440, 30),    # POCO X3 Pro
            ("Xiaomi", "2201117TY", "spes", 1080, 2400, 409, 31),     # Redmi Note 11
            ("Oppo", "CPH2127", "OP4B79", 720, 1600, 269, 29),        # A53
            ("Vivo", "V2025", "V2025", 1080, 2400, 440, 30),          # V20
            ("Realme", "RMX3363", "RMX3363", 1080, 2400, 405, 31),    # GT Master
            ("Infinix", "X680", "Infinix-X680", 720, 1640, 320, 29)   # Hot 9 (Populer di Indo)
        ]
        
        self.output_dir = "sessions/devices"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def _generate_imei(self):
        """Generate valid IMEI using Luhn checksum"""
        imei = [random.randint(0, 9) for _ in range(14)]
        checksum = sum((x if i % 2 == 0 else sum(divmod(2 * x, 10)))
                       for i, x in enumerate(imei))
        imei.append((10 - checksum % 10) % 10)
        return ''.join(map(str, imei))

    def _generate_uuid(self):
        return str(uuid.uuid4())

    def get_identity(self, username: str):
        """
        LOAD atau CREATE identity.
        Jika akun sudah punya device ID, pakai itu. Jika belum, buat baru.
        Ini kunci agar tidak kena 'Suspicious Login'.
        """
        file_path = f"{self.output_dir}/{username}_device.json"
        
        # 1. Coba load yang sudah ada
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    # Validasi simpel
                    if "brand" in data and "uuid" in data:
                        return data
            except Exception:
                pass # Jika file rusak, buat baru

        # 2. Buat baru jika belum ada
        print(f"📱 Generating NEW device identity for {username}...")
        brand, model, device, width, height, dpi, android_ver = random.choice(self.devices_db)
        
        identity = {
            "app_version": "269.0.0.18.75", # Versi IG lumayan baru
            "android_version": android_ver,
            "android_release": str(random.randint(10, 13)),
            "brand": brand,
            "manufacturer": brand,
            "model": model,
            "device": device,
            "cpu": device,
            "display_resolution": f"{width}x{height}",
            "dpi": f"{dpi}dpi",
            "phone_id": self._generate_uuid(),
            "uuid": self._generate_uuid(),
            "advertising_id": self._generate_uuid(),
            "android_device_id": f"android-{hashlib.md5(username.encode()).hexdigest()[:16]}", # Consistent hash based on username
            "imei": self._generate_imei(),
            
            # --- LOKALISASI INDONESIA (PENTING) ---
            "locale": "id_ID",
            "country": "ID",
            "timezone_offset": 25200, # UTC+7 (WIB)
        }

        # Simpan
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(identity, f, indent=2)
            
        return identity

if __name__ == "__main__":
    gen = DeviceIdentityGenerator()
    print(json.dumps(gen.get_identity("test_user"), indent=2))