#!/usr/bin/env python3
"""
Scheduled Posting - Enhanced with Background Scheduler
Fitur untuk menjadwalkan posting foto atau reels secara otomatis
Bisa jalan di background bahkan saat bot ditutup
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import os
import json
from datetime import datetime
import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

class ScheduledPost:
    def __init__(self, client=None, username=None):
        self.schedule_file = "scheduled_posts.json"
        self.scheduler = BackgroundScheduler()
        self.client = client
        self.username = username
        self.load_schedules()

    def load_schedules(self):
        """Load schedule dari file"""
        if os.path.exists(self.schedule_file):
            try:
                with open(self.schedule_file, 'r', encoding='utf-8') as f:
                    self.schedules = json.load(f)
            except:
                self.schedules = []
        else:
            self.schedules = []

    def save_schedules(self):
        """Simpan schedule ke file"""
        try:
            with open(self.schedule_file, 'w', encoding='utf-8') as f:
                json.dump(self.schedules, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            error_msg(f"Error save schedule: {str(e)}")
            return False

    def add_schedule(self, file_path, caption, post_time, post_type="photo"):
        """Tambah jadwal posting"""
        try:
            if not os.path.exists(file_path):
                error_msg(f"File tidak ditemukan: {file_path}")
                return False

            schedule = {
                "id": len(self.schedules) + 1,
                "file_path": file_path,
                "caption": caption,
                "post_time": post_time,
                "post_type": post_type,
                "created_at": datetime.now().isoformat(),
                "status": "pending"
            }

            self.schedules.append(schedule)
            if self.save_schedules():
                success_msg(f"✅ Jadwal posting berhasil ditambahkan (ID: {schedule['id']})")
                return True
            return False

        except Exception as e:
            error_msg(f"Error: {str(e)}")
            return False

    def list_schedules(self):
        """Tampilkan daftar jadwal posting"""
        if not self.schedules:
            warning_msg("Tidak ada jadwal posting")
            return

        show_separator()
        print(Fore.CYAN + "\n📋 DAFTAR JADWAL POSTING" + Style.RESET_ALL)
        show_separator()

        for schedule in self.schedules:
            status_color = Fore.GREEN if schedule['status'] == 'pending' else (Fore.BLUE if schedule['status'] == 'posted' else Fore.YELLOW)
            print(f"\nID: {schedule['id']}")
            print(f"  File: {os.path.basename(schedule['file_path'])}")
            print(f"  Type: {schedule['post_type'].upper()}")
            print(f"  Caption: {schedule['caption'][:50]}..." if len(schedule['caption']) > 50 else f"  Caption: {schedule['caption']}")
            print(f"  Jadwal: {schedule['post_time']}")
            print(status_color + f"  Status: {schedule['status'].upper()}" + Style.RESET_ALL)

    def delete_schedule(self, schedule_id):
        """Hapus jadwal posting"""
        try:
            self.schedules = [s for s in self.schedules if s['id'] != schedule_id]
            if self.save_schedules():
                success_msg(f"✅ Jadwal posting ID {schedule_id} berhasil dihapus")
                return True
            return False
        except Exception as e:
            error_msg(f"Error: {str(e)}")
            return False

    def post_scheduled_job(self, schedule_id, file_path, caption, post_type):
        """Job yang dijalankan scheduler"""
        try:
            info_msg(f"⏰ Waktu posting! Memproses jadwal ID {schedule_id}...")
            
            if post_type == 'photo':
                self.client.photo_upload(file_path, caption=caption)
            elif post_type == 'reel':
                self.client.clip_upload(file_path, caption=caption)
            
            # Update status schedule
            for schedule in self.schedules:
                if schedule['id'] == schedule_id:
                    schedule['status'] = 'posted'
                    schedule['posted_at'] = datetime.now().isoformat()
            
            self.save_schedules()
            success_msg(f"✅ Posting berhasil! (ID: {schedule_id})")
            
        except Exception as e:
            error_msg(f"❌ Error posting (ID: {schedule_id}): {str(e)}")
            for schedule in self.schedules:
                if schedule['id'] == schedule_id:
                    schedule['status'] = 'failed'
                    schedule['error'] = str(e)
            self.save_schedules()

    def start_background_scheduler(self):
        """Mulai background scheduler"""
        try:
            if self.scheduler.running:
                warning_msg("Scheduler sudah berjalan!")
                return False
            
            self.load_schedules()
            
            if not self.schedules:
                warning_msg("Tidak ada jadwal posting")
                return False
            
            info_msg("Memulai background scheduler...")
            
            for schedule in self.schedules:
                if schedule['status'] == 'pending':
                    try:
                        # Parse waktu: "2025-11-11 14:30"
                        post_datetime = datetime.strptime(schedule['post_time'], "%Y-%m-%d %H:%M")
                        hour = post_datetime.hour
                        minute = post_datetime.minute
                        
                        # Schedule dengan cron
                        self.scheduler.add_job(
                            self.post_scheduled_job,
                            CronTrigger(hour=hour, minute=minute),
                            args=[
                                schedule['id'],
                                schedule['file_path'],
                                schedule['caption'],
                                schedule['post_type']
                            ],
                            id=f"scheduled_post_{schedule['id']}"
                        )
                        
                        info_msg(f"✅ Jadwal ID {schedule['id']} terdaftar: {schedule['post_time']}")
                    except Exception as e:
                        error_msg(f"Error schedule ID {schedule['id']}: {str(e)}")
            
            self.scheduler.start()
            success_msg("✅ Background scheduler dimulai!")
            return True
            
        except Exception as e:
            error_msg(f"Error start scheduler: {str(e)}")
            return False

    def stop_scheduler(self):
        """Hentikan background scheduler"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                success_msg("✅ Scheduler dihentikan")
                return True
            else:
                warning_msg("Scheduler tidak berjalan")
                return False
        except Exception as e:
            error_msg(f"Error stop scheduler: {str(e)}")
            return False

    def get_scheduler_status(self):
        """Cek status scheduler"""
        if self.scheduler.running:
            return f"🟢 AKTIF ({len(self.scheduler.get_jobs())} job aktif)"
        else:
            return "🔴 TIDAK AKTIF"

# Global scheduler instance
global_scheduler = None

def scheduled_posting_menu(client, username):
    """Menu scheduled posting"""
    global global_scheduler
    
    scheduler = ScheduledPost(client, username)

    while True:
        clear_screen = lambda: os.system('cls' if os.name == 'nt' else 'clear')
        clear_screen()
        
        show_separator()
        print(Fore.CYAN + "\n⏰ SCHEDULED POSTING" + Style.RESET_ALL)
        show_separator()
        print(Fore.YELLOW + f"\nStatus Scheduler: {scheduler.get_scheduler_status()}" + Style.RESET_ALL)
        show_separator()
        print(Fore.YELLOW + "\n1. 📅 Jadwalkan Posting Foto")
        print("2. 🎥 Jadwalkan Posting Reels")
        print("3. 📋 Lihat Daftar Jadwal")
        print("4. 🗑️  Hapus Jadwal")
        print("5. ▶️  Mulai Background Scheduler")
        print("6. ⏹️  Hentikan Background Scheduler")
        print("7. 📊 Status Aktif Scheduler")
        print("0. ❌ Kembali" + Style.RESET_ALL)
        show_separator()

        choice = input(Fore.MAGENTA + "\nPilih menu (0-7): " + Style.RESET_ALL).strip()

        if choice == '0':
            info_msg("Kembali...")
            break
        elif choice == '1':
            clear_screen()
            schedule_photo(scheduler)
        elif choice == '2':
            clear_screen()
            schedule_reel(scheduler)
        elif choice == '3':
            clear_screen()
            scheduler.list_schedules()
        elif choice == '4':
            clear_screen()
            delete_schedule(scheduler)
        elif choice == '5':
            clear_screen()
            global_scheduler = scheduler
            scheduler.start_background_scheduler()
        elif choice == '6':
            clear_screen()
            scheduler.stop_scheduler()
        elif choice == '7':
            clear_screen()
            show_separator()
            print(Fore.CYAN + "\n📊 STATUS SCHEDULER" + Style.RESET_ALL)
            show_separator()
            print(f"Status: {scheduler.get_scheduler_status()}")
            if scheduler.scheduler.running:
                jobs = scheduler.scheduler.get_jobs()
                print(f"\nJob Aktif: {len(jobs)}")
                for job in jobs:
                    print(f"  - {job.id}")
        else:
            clear_screen()
            error_msg("Pilihan tidak valid!")

        input(Fore.CYAN + "\nTekan Enter untuk lanjut..." + Style.RESET_ALL)

def schedule_photo(scheduler):
    """Jadwalkan posting foto"""
    try:
        posts_folder = "posts_photos"
        if not os.path.exists(posts_folder):
            error_msg(f"Folder {posts_folder} tidak ditemukan")
            return

        image_files = [f for f in os.listdir(posts_folder) 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]

        if not image_files:
            warning_msg(f"Tidak ada file di folder {posts_folder}")
            return

        print(Fore.YELLOW + "\n📁 Pilih foto:" + Style.RESET_ALL)
        for i, file in enumerate(image_files, 1):
            print(f"{i}. {file}")
        
        choice = input(Fore.MAGENTA + "\nPilih foto (nomor): " + Style.RESET_ALL).strip()
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(image_files):
                file_path = os.path.join(posts_folder, image_files[choice_num - 1])
            else:
                error_msg("Pilihan tidak valid!")
                return
        except ValueError:
            error_msg("Input harus angka!")
            return

        caption = input(Fore.YELLOW + "\nCaption: " + Style.RESET_ALL).strip()
        
        print(Fore.YELLOW + "\nFormat waktu: YYYY-MM-DD HH:MM")
        print("Contoh: 2025-11-11 14:30" + Style.RESET_ALL)
        post_time = input(Fore.YELLOW + "Waktu posting: " + Style.RESET_ALL).strip()

        try:
            datetime.strptime(post_time, "%Y-%m-%d %H:%M")
        except ValueError:
            error_msg("Format waktu tidak valid!")
            return

        if scheduler.add_schedule(file_path, caption, post_time, "photo"):
            success_msg("Jadwal foto berhasil ditambahkan!")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def schedule_reel(scheduler):
    """Jadwalkan posting reels"""
    try:
        reels_folder = "posts_reels"
        if not os.path.exists(reels_folder):
            error_msg(f"Folder {reels_folder} tidak ditemukan")
            return

        video_files = [f for f in os.listdir(reels_folder) 
                      if f.lower().endswith(('.mp4', '.mov', '.avi'))]

        if not video_files:
            warning_msg(f"Tidak ada file di folder {reels_folder}")
            return

        print(Fore.YELLOW + "\n📁 Pilih reels:" + Style.RESET_ALL)
        for i, file in enumerate(video_files, 1):
            print(f"{i}. {file}")
        
        choice = input(Fore.MAGENTA + "\nPilih reels (nomor): " + Style.RESET_ALL).strip()
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(video_files):
                file_path = os.path.join(reels_folder, video_files[choice_num - 1])
            else:
                error_msg("Pilihan tidak valid!")
                return
        except ValueError:
            error_msg("Input harus angka!")
            return

        caption = input(Fore.YELLOW + "\nCaption: " + Style.RESET_ALL).strip()
        
        print(Fore.YELLOW + "\nFormat waktu: YYYY-MM-DD HH:MM")
        print("Contoh: 2025-11-11 14:30" + Style.RESET_ALL)
        post_time = input(Fore.YELLOW + "Waktu posting: " + Style.RESET_ALL).strip()

        try:
            datetime.strptime(post_time, "%Y-%m-%d %H:%M")
        except ValueError:
            error_msg("Format waktu tidak valid!")
            return

        if scheduler.add_schedule(file_path, caption, post_time, "reel"):
            success_msg("Jadwal reels berhasil ditambahkan!")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def delete_schedule(scheduler):
    """Hapus jadwal posting"""
    scheduler.list_schedules()
    
    schedule_id = input(Fore.MAGENTA + "\nMasukkan ID jadwal yang mau dihapus: " + Style.RESET_ALL).strip()
    try:
        schedule_id = int(schedule_id)
        scheduler.delete_schedule(schedule_id)
    except ValueError:
        error_msg("ID harus angka!")
