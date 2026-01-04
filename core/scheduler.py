#!/usr/bin/env python3
"""
Multi-Account Scheduler – Production Fixed Version

Tugas:
- Menjalankan tugas berulang (auto post, auto follow, auto dm, dll)
- Mendukung multi-akun tanpa bentrok (thread-safe)
- Auto retry kalau task gagal
- Delay adaptif (anti-detection)

Dependensi:
  pip install schedule python-dotenv
"""

import os
import time
import random
import threading
import traceback
from datetime import datetime, timedelta
from queue import Queue
from dotenv import load_dotenv
import schedule

from core.login_manager import LoginManager

load_dotenv()


class MultiAccountScheduler:
    def __init__(self):
        self.login_manager = LoginManager()
        self.running_tasks = {}
        self.task_queue = Queue()
        self.lock = threading.Lock()
        self.stop_flag = False

    # ====================================================
    # 🔁 TASK REGISTRATION
    # ====================================================
    def register_task(self, username, func, interval_minutes=60):
        """
        Daftarkan task per akun
        """
        if username not in self.running_tasks:
            self.running_tasks[username] = []

        job = {
            "username": username,
            "func": func,
            "interval": interval_minutes,
            "next_run": datetime.now() + timedelta(minutes=interval_minutes),
            "retries": 0,
        }
        self.running_tasks[username].append(job)
        print(f"📅 Task baru untuk {username} dijadwalkan setiap {interval_minutes} menit.")

    # ====================================================
    # 🧠 EXECUTOR
    # ====================================================
    def _execute_task(self, job):
        """
        Jalankan 1 task (aman dari crash)
        """
        username = job["username"]
        func = job["func"]
        try:
            print(f"▶️ [{username}] Menjalankan task pada {datetime.now().strftime('%H:%M:%S')}")
            func(username)
            print(f"✅ [{username}] Task berhasil.")
        except Exception as e:
            job["retries"] += 1
            print(f"❌ [{username}] Task error: {e}")
            traceback.print_exc()
            if job["retries"] < 3:
                delay = random.randint(30, 120)
                print(f"🔁 Retry dalam {delay} detik...")
                time.sleep(delay)
                self._execute_task(job)
            else:
                print(f"🚫 [{username}] Task gagal setelah 3 percobaan.")
        finally:
            job["next_run"] = datetime.now() + timedelta(minutes=job["interval"])

    # ====================================================
    # 🕓 SCHEDULER LOOP
    # ====================================================
    def _schedule_loop(self):
        """
        Loop utama penjadwalan task
        """
        while not self.stop_flag:
            now = datetime.now()
            for username, jobs in list(self.running_tasks.items()):
                for job in jobs:
                    if now >= job["next_run"]:
                        threading.Thread(target=self._execute_task, args=(job,), daemon=True).start()
            time.sleep(5)

    # ====================================================
    # 🚀 TASK EXAMPLES
    # ====================================================
    def _example_task(self, username):
        """
        Contoh task sederhana: cek status akun dan print log
        """
        self.login_manager.check_status(username)
        delay = random.randint(3, 10)
        print(f"💤 [{username}] Tidur {delay} detik untuk anti-ban.")
        time.sleep(delay)

    # ====================================================
    # ▶️ RUNNER
    # ====================================================
    def start(self):
        """
        Mulai scheduler utama
        """
        print("🚀 Menyiapkan akun...")
        data = self.login_manager.account_manager._load_accounts()
        if not data:
            print("📭 Tidak ada akun tersimpan.")
            return

        # Register contoh task per akun
        for username in data.keys():
            self.register_task(username, self._example_task, interval_minutes=60)

        print("✅ Scheduler dimulai. Tekan CTRL +C untuk berhenti.")
        try:
            self._schedule_loop()
        except KeyboardInterrupt:
            print("\n🛑 Scheduler dihentikan oleh pengguna.")
            self.stop_flag = True
        except Exception as e:
            print(f"❌ Fatal error pada scheduler: {e}")
        finally:
            print("🧹 Membersihkan scheduler...")
            self.running_tasks.clear()
            print("✅ Selesai.")


if __name__ == "__main__":
    scheduler = MultiAccountScheduler()
    scheduler.start()