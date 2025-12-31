#!/usr/bin/env python3
"""
Scheduled Post IG - Integrasi Cronjob
Jalankan ini via cron untuk post otomatis.
Contoh post foto dengan caption.
"""

import os
import random
from datetime import datetime
from instagrapi import Client
from dotenv import load_dotenv

load_dotenv()

# Config
SESSION_FILE = "instagram_session.json"  # Dari login sebelumnya
PHOTO_DIR = "photos"  # Folder foto untuk post
CAPTIONS = [
    "Caption random 1",
    "Caption random 2",
    # Tambah caption lu di sini
]

def main():
    if not os.path.exists(SESSION_FILE):
        print("Session file tidak ada! Login dulu via dashboard.py")
        return

    cl = Client()
    cl.load_settings(SESSION_FILE)

    # Pilih random foto dari dir
    photos = [f for f in os.listdir(PHOTO_DIR) if f.endswith(('.jpg', '.png'))]
    if not photos:
        print("Tidak ada foto di folder photos!")
        return

    photo_path = os.path.join(PHOTO_DIR, random.choice(photos))
    caption = random.choice(CAPTIONS)

    try:
        cl.photo_upload(photo_path, caption=caption)
        print(f"Post berhasil pada {datetime.now()}")
    except Exception as e:
        print(f"Error post: {str(e)}")

if __name__ == "__main__":
    main()