#!/usr/bin/env python3
"""
Device Identity Generator - Production Fixed Version

Generate completely random Android-like device identities
for each Instagram account with valid UUID, IMEI (Luhn checksum),
MAC address, and other required fields.
Compatible with Termux & Windows.
"""

import json
import random
import string
import uuid
import hashlib
from datetime import datetime

class DeviceIdentityGenerator:
    def __init__(self):
        self.android_versions = [9, 10, 11, 12, 13]
        self.brands = [
            ("Samsung", "SM-G991B", "r0q"),
            ("Xiaomi", "M2012K11AG", "venus"),
            ("Oppo", "CPH2231", "ossi"),
            ("Vivo", "V2109", "pd2069f"),
            ("Realme", "RMX3081", "rmx3081")
        ]

    def _generate_imei(self):
        """Generate valid IMEI using Luhn checksum"""
        imei = [random.randint(0, 9) for _ in range(14)]
        checksum = sum((x if i % 2 == 0 else sum(divmod(2 * x, 10)))
                       for i, x in enumerate(imei))
        imei.append((10 - checksum % 10) % 10)
        return ''.join(map(str, imei))

    def _generate_mac(self):
        """Generate valid MAC address"""
        return ":".join(f"{random.randint(0, 255):02x}" for _ in range(6))

    def _generate_android_device_id(self):
        return f"android-{''.join(random.choices('0123456789abcdef', k=16))}"

    def _generate_uuid(self):
        return str(uuid.uuid4())

    def _generate_hash(self, value):
        return hashlib.md5(value.encode()).hexdigest()

    def generate_identity(self):
        brand, model, device = random.choice(self.brands)
        android_version = random.choice(self.android_versions)
        identity = {
            "brand": brand,
            "manufacturer": brand,
            "model": model,
            "device": device,
            "android_version": android_version,
            "phone_id": self._generate_uuid(),
            "uuid": self._generate_uuid(),
            "client_session_id": self._generate_uuid(),
            "advertising_id": self._generate_uuid(),
            "android_device_id": self._generate_android_device_id(),
            "mac_address": self._generate_mac(),
            "imei": self._generate_imei(),
            "creation_time": datetime.utcnow().isoformat(),
        }
        # Add a unique hash ID to prevent duplicates
        identity["unique_hash"] = self._generate_hash(identity["uuid"] + identity["android_device_id"])
        return identity

    def save_identity(self, username, output_dir="sessions"):
        identity = self.generate_identity()
        path = f"{output_dir}/{username}_identity.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(identity, f, indent=2)
        return path


if __name__ == "__main__":
    gen = DeviceIdentityGenerator()
    sample = gen.generate_identity()
    print(json.dumps(sample, indent=2))