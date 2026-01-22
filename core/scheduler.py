#!/usr/bin/env python3
"""
Multi-Account Scheduler – Enhanced Human Version
Fitur:
- Circadian Rhythm (Bot tidur malam, aktif siang)
- Interval Jitter (Waktu tidak pernah pas/tepat)
- Thread Pool Executor (Lebih stabil daripada raw threading)
"""

import time
import random
import threading
import logging
from datetime import datetime, timedelta
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor

# Setup Logger
logger = logging.getLogger(__name__)

class MultiAccountScheduler:
    def __init__(self, max_workers=5):
        self.running_tasks = {} # {username: [job1, job2]}
        self.stop_flag = False
        self.lock = threading.Lock()
        
        # Executor untuk menjalankan task secara paralel tapi terkontrol
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Konfigurasi Jam Kerja (WIB/Local Time)
        self.work_start_hour = 7  # Mulai jam 7 pagi
        self.work_end_hour = 23   # Tidur jam 11 malam

    # ====================================================
    # 🧠 HUMAN LOGIC
    # ====================================================
    def _is_working_hours(self):
        """Cek apakah sekarang waktunya bot bekerja"""
        current_hour = datetime.now().hour
        # Bot istirahat antara jam 23:00 sampai 07:00
        if self.work_start_hour <= current_hour < self.work_end_hour:
            return True
        return False

    def _get_jittered_interval(self, base_interval_minutes):
        """
        Menambahkan variasi waktu acak (Jitter).
        Jika interval 60 menit, hasilnya bisa 45-75 menit.
        """
        variance = base_interval_minutes * 0.25 # Variasi 25%
        jitter = random.uniform(-variance, variance)
        return max(1, base_interval_minutes + jitter) # Minimal 1 menit

    # ====================================================
    # 🔁 TASK MANAGEMENT
    # ====================================================
    def register_task(self, username, task_name, func, base_interval=60):
        """
        Mendaftarkan tugas baru untuk akun tertentu.
        """
        with self.lock:
            if username not in self.running_tasks:
                self.running_tasks[username] = []

            # Hitung waktu jalan pertama (sedikit diacak agar tidak semua akun mulai barengan)
            first_delay = random.uniform(0.5, 5.0) 
            next_run = datetime.now() + timedelta(minutes=first_delay)

            job = {
                "id": f"{username}_{task_name}",
                "username": username,
                "task_name": task_name,
                "func": func,
                "base_interval": base_interval,
                "next_run": next_run,
                "status": "pending"
            }
            
            self.running_tasks[username].append(job)
            logger.info(f"📅 Scheduled '{task_name}' for @{username} (Base: {base_interval}m)")

    def get_next_task(self):
        """
        (Untuk Main Loop) Mengambil task yang siap dijalankan sekarang.
        """
        now = datetime.now()
        
        # Cek apakah bot harus tidur?
        if not self._is_working_hours():
            # Jika sedang jam tidur, return None (tapi sesekali bisa bangun untuk cek notif - future improvement)
            return None

        with self.lock:
            for username, jobs in self.running_tasks.items():
                for job in jobs:
                    if job["status"] == "pending" and now >= job["next_run"]:
                        # Tandai sebagai running agar tidak diambil worker lain
                        job["status"] = "running"
                        return job
        return None

    def complete_task(self, job_id):
        """
        Menandai task selesai dan menjadwalkan ulang dengan waktu acak.
        """
        with self.lock:
            for username, jobs in self.running_tasks.items():
                for job in jobs:
                    if job["id"] == job_id:
                        # Jadwalkan ulang
                        interval = self._get_jittered_interval(job["base_interval"])
                        job["next_run"] = datetime.now() + timedelta(minutes=interval)
                        job["status"] = "pending"
                        
                        logger.info(f"✅ Finished {job['id']}. Next run in {interval:.1f} mins ({job['next_run'].strftime('%H:%M')})")
                        return

    # ====================================================
    # 🚀 EXECUTOR (Called by Main.py)
    # ====================================================
    # Di arsitektur baru ini, Scheduler hanya "Pemberi Tugas".
    # Eksekusi (login, client calls) dilakukan di Main.py / BotController
    # agar lebih terpusat dan mudah di-stop.

    def get_pending_tasks_count(self):
        count = 0
        for jobs in self.running_tasks.values():
            count += len(jobs)
        return count

if __name__ == "__main__":
    # Test Unit
    logging.basicConfig(level=logging.INFO)
    s = MultiAccountScheduler()
    print(f"Working hours? {s._is_working_hours()}")
    print(f"Jittered 60m: {s._get_jittered_interval(60)}")