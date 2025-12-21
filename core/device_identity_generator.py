#!/usr/bin/env python3
"""
Device Identity Generator - Production Version

Generate completely random Android-like device identities
untuk setiap akun Instagram, dengan 20+ field unik dan valid
(IMEI pakai Luhn checksum, MAC format benar, dll).
"""

import json
import random
import string
from pathlib import Path
from typing import Dict, Any, Optional


class DeviceIdentityGenerator:
    """
    Generator identitas device:
    - Load device database (data/device_db_full.json)
    - Pilih random model (Samsung/Xiaomi/Oppo/etc)
    - Generate ID unik: device_id, android_id, gsf_id, IMEI, MAC, serial, fingerprint, dll
    - Save/Load identity per-username (persistent)
    """

    def __init__(self, device_db_path: str = "data/device_db_full.json"):
        self.device_db_path = Path(device_db_path)
        self.identity_dir = Path("sessions/account_identities")
        self.identity_dir.mkdir(parents=True, exist_ok=True)

        self.device_db = self._load_device_db()

    # ======================================================================
    # Internal helpers
    # ======================================================================

    def _load_device_db(self) -> list:
        """Load database device dari JSON. Kalau tidak ada, pakai fallback minimal."""
        try:
            if self.device_db_path.exists():
                with open(self.device_db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and data:
                        return data
        except Exception:
            pass

        # Fallback minimal (supaya generator tetap jalan)
        return [
            {
                "id": 1,
                "brand": "samsung",
                "manufacturer": "Samsung",
                "model": "SM-G991B",
                "device": "r0q",
                "product": "r0qxx",
                "android_version": 12,
                "cpu": "Exynos 2100",
                "ram_gb": 8,
                "rom_gb": 256,
                "premium": True,
            }
        ]

    def _random_hex(self, length: int) -> str:
        return "".join(random.choice("0123456789abcdef") for _ in range(length))

    def _random_digits(self, length: int) -> str:
        return "".join(random.choice(string.digits) for _ in range(length))

    def _random_alnum(self, length: int) -> str:
        chars = string.ascii_uppercase + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    # ======================================================================
    # IMEI + Luhn checksum
    # ======================================================================

    def _luhn_checksum(self, number: str) -> int:
        """
        Hitung checksum Luhn untuk IMEI.
        number: 14 digit pertama IMEI (tanpa checksum).
        """
        digits = [int(d) for d in number]
        for i in range(len(digits) - 1, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        total = sum(digits)
        return (10 - (total % 10)) % 10

    def _generate_random_imei(self) -> str:
        """
        Generate IMEI 15 digit valid (Luhn correct).
        """
        base = self._random_digits(14)
        checksum = self._luhn_checksum(base)
        return base + str(checksum)

    # ======================================================================
    # MAC, Serial, Fingerprint
    # ======================================================================

    def _generate_random_mac(self) -> str:
        """Generate MAC address: XX:XX:XX:XX:XX:XX"""
        return ":".join(self._random_hex(2) for _ in range(6))

    def _generate_random_serial(self) -> str:
        """Generate serial number 16 char alphanumeric"""
        return self._random_alnum(16)

    def _generate_random_fingerprint(self, device: Dict[str, Any]) -> str:
        """
        Generate Android build fingerprint dari info device.
        Format kira-kira:
        brand/device/model:version/sdk/build_id:user/release-keys
        """
        brand = device.get("brand", "samsung")
        device_name = device.get("device", device.get("model", "generic"))
        model = device.get("model", "SM-G991B")
        android_version = device.get("android_version", 12)

        sdk = {
            10: 29,
            11: 30,
            12: 31,
            13: 33,
            14: 34,
        }.get(android_version, 31)

        build_id = self._random_alnum(6)
        return f"{brand}/{device_name}/{model}:{android_version}/" \
               f"{sdk}/{build_id}:user/release-keys"

    # ======================================================================
    # Public API
    # ======================================================================

    def generate_completely_random_identity(self) -> Dict[str, Any]:
        """
        Generate identitas device random total:
        - Pilih random device dari DB
        - Generate semua ID unik
        """
        device = random.choice(self.device_db)

        identity: Dict[str, Any] = {}

        # Base device info
        identity["brand"] = device.get("brand")
        identity["manufacturer"] = device.get("manufacturer")
        identity["model"] = device.get("model")
        identity["device"] = device.get("device")
        identity["product"] = device.get("product")
        identity["android_version"] = device.get("android_version")
        identity["cpu"] = device.get("cpu")
        identity["ram_gb"] = device.get("ram_gb")
        identity["rom_gb"] = device.get("rom_gb")
        identity["premium"] = device.get("premium", False)

        # IDs
        identity["device_id"] = self._random_hex(16)
        identity["android_id"] = self._random_hex(16)
        identity["gsf_id"] = self._random_digits(8)
        identity["phone_id"] = self._random_hex(32)

        # IMEI
        identity["imei_1"] = self._generate_random_imei()
        identity["imei_2"] = self._generate_random_imei()

        # MAC & serial
        identity["mac_wifi"] = self._generate_random_mac()
        identity["mac_bluetooth"] = self._generate_random_mac()
        identity["serial_number"] = self._generate_random_serial()

        # Fingerprint & build
        identity["fingerprint"] = self._generate_random_fingerprint(device)
        identity["build_id"] = identity["fingerprint"].split("/")[-2].split(":")[0]

        # Tambahan yang sering dipakai fingerprinting
        identity["timezone"] = "Asia/Jakarta"
        identity["locale"] = "id_ID"
        identity["sim_operator"] = random.choice(
            ["51001", "51010", "51011", "51021", "51089"]
        )  # beberapa MCC/MNC Indonesia
        identity["carrier"] = random.choice(
            ["Telkomsel", "Indosat", "XL", "Tri", "Smartfren"]
        )

        return identity

    # ======================================================================
    # Persistence per-akun
    # ======================================================================

    def _identity_path(self, username: str) -> Path:
        safe = "".join(c for c in username if c.isalnum() or c in ("_", "-", "."))
        return self.identity_dir / f"{safe}.json"

    def save_identity(self, username: str, identity: Dict[str, Any]) -> str:
        """Save identity ke file JSON per-username."""
        path = self._identity_path(username)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(identity, f, indent=2, ensure_ascii=False)
        return str(path)

    def load_identity(self, username: str) -> Optional[Dict[str, Any]]:
        """Load identity kalau file ada, kalau tidak return None."""
        path = self._identity_path(username)
        if not path.exists():
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def delete_identity(self, username: str) -> bool:
        """Delete identity file untuk username tertentu."""
        path = self._identity_path(username)
        if path.exists():
            try:
                path.unlink()
                return True
            except Exception:
                return False
        return False

    def get_or_create_identity(self, username: str) -> Dict[str, Any]:
        """
        Kalau identity sudah ada → load.
        Kalau belum → generate baru lalu save.
        """
        existing = self.load_identity(username)
        if existing:
            return existing

        identity = self.generate_completely_random_identity()
        self.save_identity(username, identity)
        return identity


def create_device_identity_generator() -> DeviceIdentityGenerator:
    """Factory kecil biar konsisten dipanggil dari luar."""
    return DeviceIdentityGenerator()