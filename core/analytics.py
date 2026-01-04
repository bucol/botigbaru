#!/usr/bin/env python3
"""
Analytics Core - Production Fixed Version

Tugas:
- Melacak statistik akun (followers, likes, comments, posts)
- Menghitung growth & engagement rate
- Menyimpan log harian di logs/stats.json
- Kompatibel Termux & Windows

Dependensi:
  pip install python-dotenv
"""

import os
import json
from datetime import datetime, timedelta
from collections import defaultdict
from statistics import mean


class Analytics:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        self.stats_file = os.path.join(log_dir, "stats.json")
        os.makedirs(log_dir, exist_ok=True)
        self.stats = self._load_stats()

    # =====================================================
    # 📦 FILE HANDLER
    # =====================================================
    def _load_stats(self):
        """Load file stats.json"""
        if not os.path.exists(self.stats_file):
            with open(self.stats_file, "w", encoding="utf-8") as f:
                json.dump({}, f)
            return {}
        try:
            with open(self.stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ File stats.json korup, membuat ulang baru.")
            return {}

    def _save_stats(self):
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)

    # =====================================================
    # 🧩 RECORD & UPDATE
    # =====================================================
    def record_daily_stats(self, username, followers, following, posts, likes, comments):
        """Rekam statistik harian akun"""
        today = datetime.now().strftime("%Y-%m-%d")
        if username not in self.stats:
            self.stats[username] = {}
        self.stats[username][today] = {
            "followers": followers,
            "following": following,
            "posts": posts,
            "likes": likes,
            "comments": comments,
        }
        self._save_stats()
        print(f"📈 Statistik {username} diperbarui ({today}).")

    # =====================================================
    # 📊 GROWTH CALCULATION
    # =====================================================
    def _calc_growth(self, data):
        """Hitung growth harian"""
        days = sorted(data.keys())
        if len(days) < 2:
            return 0
        today, yesterday = days[-1], days[-2]
        f_today = data[today]["followers"]
        f_yesterday = data[yesterday]["followers"]
        return f_today - f_yesterday

    def _calc_engagement(self, data):
        """Hitung engagement rate (likes + comments / followers)"""
        days = sorted(data.keys())
        if not days:
            return 0.0
        total_likes = sum(v["likes"] for v in data.values())
        total_comments = sum(v["comments"] for v in data.values())
        avg_followers = mean(v["followers"] for v in data.values())
        if avg_followers == 0:
            return 0.0
        return round(((total_likes + total_comments) / (avg_followers * len(days))) * 100, 2)

    # =====================================================
    # 🧠 ANALYTICS SUMMARY
    # =====================================================
    def get_summary(self, username):
        """Ambil ringkasan analytics akun"""
        if username not in self.stats:
            print(f"⚠️ Tidak ada data untuk {username}")
            return None
        data = self.stats[username]
        growth = self._calc_growth(data)
        engagement = self._calc_engagement(data)
        last_day = sorted(data.keys())[-1]
        last_stats = data[last_day]
        summary = {
            "username": username,
            "followers": last_stats["followers"],
            "following": last_stats["following"],
            "posts": last_stats["posts"],
            "growth": growth,
            "engagement_rate": engagement,
            "last_updated": last_day,
        }
        return summary

    # =====================================================
    # 📋 REPORT DISPLAY
    # =====================================================
    def print_report(self, username):
        """Tampilkan laporan akun"""
        summary = self.get_summary(username)
        if not summary:
            return
        print("\n📊 Laporan Analytics Akun")
        print("=" * 35)
        print(f"👤 Username: {summary['username']}")
        print(f"👥 Followers: {summary['followers']}")
        print(f"➡️ Following: {summary['following']}")
        print(f"🖼️ Posts: {summary['posts']}")
        print(f"📈 Growth (24h): {summary['growth']:+}")
        print(f"💬 Engagement Rate: {summary['engagement_rate']}%")
        print(f"🕓 Last Updated: {summary['last_updated']}")
        print("=" * 35)


if __name__ == "__main__":
    analytics = Analytics()

    # Simulasi input manual untuk testing
    print("\n=== Analytics CLI ===")
    while True:
        print("\n1️⃣ Tambah data harian\n2️⃣ Tampilkan laporan\n0️⃣ Keluar")
        choice = input("Pilih opsi: ").strip()
        if choice == "1":
            user = input("Username: ")
            followers = int(input("Followers: "))
            following = int(input("Following: "))
            posts = int(input("Jumlah post: "))
            likes = int(input("Likes total hari ini: "))
            comments = int(input("Comments total hari ini: "))
            analytics.record_daily_stats(user, followers, following, posts, likes, comments)
        elif choice == "2":
            user = input("Username: ")
            analytics.print_report(user)
        elif choice == "0":
            print("👋 Keluar dari Analytics CLI.")
            break
        else:
            print("❌ Pilihan tidak valid.")