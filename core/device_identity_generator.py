#!/usr/bin/env python3
"""
Device Identity Generator - LSPosed/Android Faker Level
Setiap akun: completely random identity (20+ field unik)
Production-grade dengan error handling & cross-platform support
"""

import random
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class DeviceIdentityGenerator:
    """Generate unik device identity per akun (safe + robust)"""
    
    def __init__(self, device_db_path: str = 'data/device_db_full.json'):
        self.device_db_path = device_db_path
        self.device_db = self._load_device_db()
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create semua folder yang diperlukan (safe cross-platform)"""
        try:
            Path('data').mkdir(parents=True, exist_ok=True)
            Path('sessions/account_identities').mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️ Warning saat create directory: {e}")
    
    def _load_device_db(self) -> list:
        """Load device DB dengan error handling"""
        try:
            db_path = Path(self.device_db_path)
            if db_path.exists():
                with open(db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        print(f"✅ Loaded {len(data)} devices dari DB")
                        return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ Error loading device DB: {e}. Fallback ke default.")
        
        return self._generate_default_db()
    
    def _generate_default_db(self) -> list:
        """Fallback device pool (lengkap)"""
        devices = [
            # Samsung - Flagship
            {"brand": "samsung", "manufacturer": "Samsung", "model": "SM-G991B", "device": "r0q", "product": "r0qxx", "android_version": 12, "cpu": "Exynos 2100", "premium": True},
            {"brand": "samsung", "manufacturer": "Samsung", "model": "SM-G950F", "device": "dreamlte", "product": "dreamlteks", "android_version": 9, "cpu": "Snapdragon 835", "premium": True},
            # Samsung - Mid
            {"brand": "samsung", "manufacturer": "Samsung", "model": "SM-A136B", "device": "a13", "product": "a13xx", "android_version": 11, "cpu": "Exynos 850", "premium": False},
            {"brand": "samsung", "manufacturer": "Samsung", "model": "SM-A515F", "device": "a51", "product": "a51xx", "android_version": 10, "cpu": "Exynos 9611", "premium": False},
            # Xiaomi - Flagship
            {"brand": "xiaomi", "manufacturer": "Xiaomi", "model": "M2101K9AG", "device": "venus", "product": "venus", "android_version": 11, "cpu": "Snapdragon 870", "premium": True},
            {"brand": "xiaomi", "manufacturer": "Xiaomi", "model": "M2012K11AG", "device": "star", "product": "star", "android_version": 11, "cpu": "Snapdragon 888", "premium": True},
            # Xiaomi - Budget
            {"brand": "xiaomi", "manufacturer": "Xiaomi", "model": "M2101K7AG", "device": "mojito", "product": "mojito", "android_version": 11, "cpu": "Snapdragon 678", "premium": False},
            {"brand": "xiaomi", "manufacturer": "Xiaomi", "model": "M2003J15SC", "device": "picasso", "product": "picasso", "android_version": 10, "cpu": "Snapdragon 730G", "premium": False},
            # Oppo
            {"brand": "oppo", "manufacturer": "OPPO", "model": "CPH2269", "device": "a54", "product": "a54", "android_version": 10, "cpu": "MediaTek Helio G85", "premium": False},
            {"brand": "oppo", "manufacturer": "OPPO", "model": "CPH2127", "device": "find_x2_pro", "product": "find_x2_pro", "android_version": 11, "cpu": "Snapdragon 865", "premium": True},
            # Vivo
            {"brand": "vivo", "manufacturer": "vivo", "model": "V2120", "device": "PD2105F", "product": "PD2105F", "android_version": 11, "cpu": "Snapdragon 662", "premium": False},
            {"brand": "vivo", "manufacturer": "vivo", "model": "V2135", "device": "PD2023", "product": "PD2023", "android_version": 12, "cpu": "MediaTek Dimensity 1200", "premium": True},
            # Realme
            {"brand": "realme", "manufacturer": "realme", "model": "RMX2185", "device": "c11", "product": "c11", "android_version": 10, "cpu": "MediaTek Helio G35", "premium": False},
            {"brand": "realme", "manufacturer": "realme", "model": "RMX2151", "device": "x50_pro", "product": "x50_pro", "android_version": 11, "cpu": "Snapdragon 865", "premium": True},
            # Huawei
            {"brand": "huawei", "manufacturer": "HUAWEI", "model": "NOH-NX9", "device": "nova7", "product": "nova7", "android_version": 10, "cpu": "Kirin 985", "premium": False},
            # Motorola
            {"brand": "motorola", "manufacturer": "motorola", "model": "XT2127-1", "device": "lena", "product": "lena", "android_version": 11, "cpu": "Snapdragon 685", "premium": False},
            # OnePlus
            {"brand": "oneplus", "manufacturer": "OnePlus", "model": "IN2010", "device": "billie", "product": "billie", "android_version": 11, "cpu": "Snapdragon 888", "premium": True},
            # Apple (untuk iOS)
            {"brand": "apple", "manufacturer": "Apple", "model": "iPhone14,5", "device": "iPhone", "product": "iPhone", "ios_version": "16.4.1", "cpu": "A15 Bionic", "premium": True},
            {"brand": "apple", "manufacturer": "Apple", "model": "iPhone13,3", "device": "iPhone", "product": "iPhone", "ios_version": "15.7.1", "cpu": "A14 Bionic", "premium": True},
            {"brand": "apple", "manufacturer": "Apple", "model": "iPhone12,1", "device": "iPhone", "product": "iPhone", "ios_version": "15.0", "cpu": "A13 Bionic", "premium": False},
        ]
        return devices
    
    def generate_completely_random_identity(self, base_device: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate COMPLETELY RANDOM identity (production-safe)"""
        
        try:
            # Pilih base device
            if not base_device or not isinstance(base_device, dict):
                base_device = random.choice(self.device_db)
            
            identity = base_device.copy()
            
            # Generate identifiers (semua random, tidak follow pattern)
            identity['device_id'] = self._generate_random_device_id()
            identity['android_id'] = self._generate_random_android_id()
            identity['gsf_id'] = self._generate_random_gsf_id()
            identity['imei_1'] = self._generate_random_imei()
            identity['imei_2'] = self._generate_random_imei()
            identity['mac_wifi'] = self._generate_random_mac()
            identity['mac_bluetooth'] = self._generate_random_mac()
            identity['serial_number'] = self._generate_random_serial()
            identity['board'] = self._generate_random_board()
            identity['display'] = self._generate_random_display()
            identity['fingerprint'] = self._generate_random_fingerprint(identity)
            identity['build_number'] = self._generate_random_build()
            identity['baseband_version'] = self._generate_random_baseband()
            identity['kernel_version'] = self._generate_random_kernel()
            identity['host'] = self._generate_random_host()
            identity['build_tags'] = 'release-keys'
            identity['screen_dpi'] = random.choice([320, 360, 420, 480, 540])
            identity['screen_size_inch'] = round(random.uniform(4.5, 6.8), 1)
            identity['ram_gb'] = random.choice([2, 3, 4, 6, 8, 12])
            identity['rom_gb'] = random.choice([32, 64, 128, 256])
            identity['identity_created'] = datetime.now().isoformat()
            identity['identity_version'] = '1.0'
            
            return identity
        
        except Exception as e:
            print(f"❌ Error generating identity: {e}")
            raise
    
    def _generate_random_device_id(self) -> str:
        return ''.join(random.choices('0123456789abcdef', k=16))
    
    def _generate_random_android_id(self) -> str:
        return ''.join(random.choices('0123456789abcdef', k=16))
    
    def _generate_random_gsf_id(self) -> str:
        return str(random.randint(10000000, 99999999))
    
    def _generate_random_imei(self) -> str:
        base = ''.join([str(random.randint(0, 9)) for _ in range(14)])
        checksum = self._luhn_checksum(base)
        return base + str(checksum)
    
    def _generate_random_mac(self) -> str:
        return ":".join(["%02x" % random.randint(0, 255) for _ in range(6)])
    
    def _generate_random_serial(self) -> str:
        return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=16))
    
    def _generate_random_board(self) -> str:
        boards = ['qcom', 'mt6785', 'mt6853', 'msm8953', 'kona', 'taro', 'lahaina', 'sdm845']
        return random.choice(boards)
    
    def _generate_random_display(self) -> str:
        prefix = random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        number = ''.join(random.choices('0123456789', k=7))
        return prefix + number
    
    def _generate_random_fingerprint(self, identity: Dict[str, Any]) -> str:
        mfr = str(identity.get('manufacturer', 'Samsung')).lower()
        device = str(identity.get('device', 'device')).lower()
        product = str(identity.get('product', 'product')).lower()
        android_ver = identity.get('android_version', 12)
        build_id = self._generate_random_display()
        
        fp = (
            f"{mfr}/{device}/{product}:{android_ver}/"
            f"{build_id}/"
            f"{''.join(random.choices('0123456789', k=8))}:"
            f"user/release-keys"
        )
        return fp
    
    def _generate_random_build(self) -> str:
        return ''.join(random.choices('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=16))
    
    def _generate_random_baseband(self) -> str:
        return 'M' + ''.join(random.choices('0123456789', k=8))
    
    def _generate_random_kernel(self) -> str:
        major = random.randint(4, 6)
        minor = random.randint(0, 20)
        patch = random.randint(0, 99)
        return f"{major}.{minor}.{patch}-android12-9-{''.join(random.choices('0123456789', k=4))}"
    
    def _generate_random_host(self) -> str:
        return ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=12))
    
    def _luhn_checksum(self, imei_base: str) -> int:
        digits = [int(d) for d in imei_base]
        digits.reverse()
        for i in range(1, len(digits), 2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        total = sum(digits)
        return (10 - (total % 10)) % 10
    
    def save_identity(self, username: str, identity: Dict[str, Any]) -> str:
        """Save identity (safe character encoding)"""
        try:
            # Validate username
            if not isinstance(username, str) or len(username) == 0:
                raise ValueError("Username invalid")
            
            identity_dir = Path('sessions/account_identities')
            identity_dir.mkdir(parents=True, exist_ok=True)
            
            # Safe filename (escape special chars)
            safe_username = "".join(c if c.isalnum() or c in '-_' else '_' for c in username)
            filepath = identity_dir / f"{safe_username}_identity.json"
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(identity, f, indent=2, ensure_ascii=False)
            
            return str(filepath)
        
        except Exception as e:
            print(f"❌ Error saving identity: {e}")
            raise
    
    def load_identity(self, username: str) -> Optional[Dict[str, Any]]:
        """Load identity (safe)"""
        try:
            safe_username = "".join(c if c.isalnum() or c in '-_' else '_' for c in username)
            filepath = Path('sessions/account_identities') / f"{safe_username}_identity.json"
            
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            return None
        
        except Exception as e:
            print(f"⚠️ Error loading identity: {e}")
            return None
    
    def delete_identity(self, username: str) -> bool:
        """Delete identity (safe)"""
        try:
            safe_username = "".join(c if c.isalnum() or c in '-_' else '_' for c in username)
            filepath = Path('sessions/account_identities') / f"{safe_username}_identity.json"
            
            if filepath.exists():
                filepath.unlink()
                return True
            
            return False
        
        except Exception as e:
            print(f"⚠️ Error deleting identity: {e}")
            return False
    
    def get_or_create_identity(self, username: str) -> Dict[str, Any]:
        """Get existing atau create baru (safe)"""
        existing = self.load_identity(username)
        if existing:
            return existing
        
        new_identity = self.generate_completely_random_identity()
        self.save_identity(username, new_identity)
        return new_identity

def create_identity_generator():
    return DeviceIdentityGenerator()
