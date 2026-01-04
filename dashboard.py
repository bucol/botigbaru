#!/usr/bin/env python3
"""
Dashboard CLI - Production Fixed Version

Tugas:
- Antarmuka utama CLI untuk semua fitur bot Instagram
- Integrasi dengan core modules (login, scheduler, analytics)
- Aman untuk Termux & Windows
"""

import os
import sys
import time
from datetime import datetime
from colorama import Fore, Style, init

# Import core modules
from core.login_manager import LoginManager
from core.account_manager import AccountManager
from core.scheduler import MultiAccountScheduler
from core.analytics import Analytics

init(autoreset=True)


class DashboardController:
    def __init__(self):
        self.account_manager = AccountManager()
        self.login_manager = LoginManager()
        self.scheduler = MultiAccountScheduler()
        self.analytics = Analytics()
        self.username = None
        self.client = None

    # =====================================================
    # 🧩 UI COMPONENTS
    # =====================================================
    def _clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def _banner(self):
        print(Fore.CYAN + Style.BRIGHT + "\n==============================")
        print(Fore.CYAN + "    🌐 BUCOL INSTAGRAM BOT")
        print(Fore.CYAN + "==============================\n" + Style.RESET_ALL)

    def _pause(self):
        input(Fore.YELLOW + "\nTekan Enter untuk kembali ke menu..." + Style.RESET_ALL)

    def _loading(self, text="Memproses"):
        print(Fore.MAGENTA + f"{text}", end="", flush=True)
        for _ in range(3):
            time.sleep(0.5)
            print(".", end="", flush=True)
        print(Style.RESET_ALL)

    # =====================================================
    # 🔑 AUTHENTICATION
    # =====================================================
    def login_menu(self):
        self._clear_screen()
        self._banner()
        print(Fore.GREEN + "🔐 LOGIN MENU" + Style.RESET_ALL)
        username = input("Masukkan username: ").strip()
        if not username:
            print("❌ Username tidak boleh kosong.")
            return
        password = input("Masukkan password: ").strip()
        if not password:
            print("❌ Password tidak boleh kosong.")
            return
        self._loading("Login")
        self.client = self.login_manager.login(username, password)
        if self.client:
            self.username = username
            print(Fore.GREEN + f"✅ Login berhasil sebagai {username}")
        else:
            print(Fore.RED + "❌ Gagal login.")
        self._pause()

    # =====================================================
    # 👤 ACCOUNT MANAGEMENT
    # =====================================================
    def account_menu(self):
        while True:
            self._clear_screen()
            self._banner()
            print(Fore.YELLOW + "👤 ACCOUNT MENU" + Style.RESET_ALL)
            print("1️⃣ Tambah akun")
            print("2️⃣ Hapus akun")
            print("3️⃣ Lihat daftar akun")
            print("4️⃣ Login semua akun")
            print("0️⃣ Kembali")
            choice = input("\nPilih opsi: ").strip()

            if choice == "1":
                u = input("Username: ")
                p = input("Password: ")
                n = input("Catatan (opsional): ")
                self.account_manager.add_account(u, p, n)
            elif choice == "2":
                u = input("Username yang dihapus: ")
                self.account_manager.remove_account(u)
            elif choice == "3":
                self.account_manager.list_accounts()
            elif choice == "4":
                self.account_manager.login_all()
            elif choice == "0":
                break
            else:
                print("❌ Pilihan tidak valid.")
            self._pause()

    # =====================================================
    # 📅 SCHEDULER
    # =====================================================
    def scheduler_menu(self):
        self._clear_screen()
        self._banner()
        print(Fore.CYAN + "📅 MULTI-ACCOUNT SCHEDULER" + Style.RESET_ALL)
        print("Scheduler akan menjalankan auto task setiap interval.")
        confirm = input("Mulai scheduler sekarang? (y/n): ").lower().strip()
        if confirm == "y":
            self._loading("Menjalankan scheduler")
            self.scheduler.start()
        else:
            print("⏸️ Scheduler dibatalkan.")
        self._pause()

    # =====================================================
    # 📊 ANALYTICS
    # =====================================================
    def analytics_menu(self):
        while True:
            self._clear_screen()
            self._banner()
            print(Fore.CYAN + "📊 ANALYTICS MENU" + Style.RESET_ALL)
            print("1️⃣ Tambah data harian")
            print("2️⃣ Tampilkan laporan akun")
            print("0️⃣ Kembali")
            choice = input("\nPilih opsi: ").strip()

            if choice == "1":
                u = input("Username: ")
                f = int(input("Followers: "))
                g = int(input("Following: "))
                p = int(input("Jumlah post: "))
                l = int(input("Likes total hari ini: "))
                c = int(input("Comments total hari ini: "))
                self.analytics.record_daily_stats(u, f, g, p, l, c)
            elif choice == "2":
                u = input("Username: ")
                self.analytics.print_report(u)
            elif choice == "0":
                break
            else:
                print("❌ Pilihan tidak valid.")
            self._pause()

    # =====================================================
    # ⚙️ MAIN MENU
    # =====================================================
    def main_menu(self):
        while True:
            self._clear_screen()
            self._banner()
            print(Fore.YELLOW + "✨ MAIN MENU" + Style.RESET_ALL)
            print("1️⃣ Login akun")
            print("2️⃣ Kelola akun")
            print("3️⃣ Jalankan scheduler")
            print("4️⃣ Lihat analytics")
            print("0️⃣ Keluar")

            choice = input("\nPilih opsi: ").strip()
            if choice == "1":
                self.login_menu()
            elif choice == "2":
                self.account_menu()
            elif choice == "3":
                self.scheduler_menu()
            elif choice == "4":
                self.analytics_menu()
            elif choice == "0":
                print("👋 Terima kasih sudah menggunakan Bucol Bot!")
                break
            else:
                print("❌ Pilihan tidak valid.")
                self._pause()


if __name__ == "__main__":
    app = DashboardController()
    app.main_menu()