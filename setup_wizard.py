#!/usr/bin/env python3
"""
IG Bot Setup Wizard
Installer otomatis & Manajemen Akun Interaktif
"""

import os
import sys
import time
import subprocess
import getpass
import json
from pathlib import Path

# --- COLORS & STYLING ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print(r"""
    ╔══════════════════════════════════════════════════╗
    ║      🤖 INSTAGRAM BOT ULTIMATE SETUP WIZARD      ║
    ║      Anti-Detect • Human Behavior • Multi-Acc    ║
    ╚══════════════════════════════════════════════════╝
    """)
    print(f"{Colors.ENDC}")

def spinner(text, duration=2):
    chars = "/—\|"
    for _ in range(duration * 10):
        for char in chars:
            sys.stdout.write(f'\r{Colors.CYAN}[{char}] {text}...{Colors.ENDC}')
            sys.stdout.flush()
            time.sleep(0.1)
    sys.stdout.write('\r' + ' ' * (len(text) + 10) + '\r')

# --- STEP 1: DEPENDENCY CHECK ---
def check_dependencies():
    print(f"{Colors.BLUE}[*] Memeriksa dependencies...{Colors.ENDC}")
    try:
        import instagrapi
        import schedule
        import dotenv
        import cryptography
        import colorama
        print(f"{Colors.GREEN}[+] Semua library sudah terinstall.{Colors.ENDC}")
    except ImportError as e:
        print(f"{Colors.WARNING}[!] Library kurang lengkap. Menginstall otomatis...{Colors.ENDC}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
            print(f"{Colors.GREEN}[+] Installasi sukses!{Colors.ENDC}")
        except Exception as install_error:
            print(f"{Colors.FAIL}[X] Gagal menginstall requirements: {install_error}{Colors.ENDC}")
            sys.exit(1)

# --- IMPORT MODULES SETELAH INSTALL ---
try:
    from core.account_manager import AccountManager
    from core.login_manager import LoginManager
    from dotenv import load_dotenv
except ImportError:
    # Fallback jika baru pertama run dan module belum terbaca
    print(f"{Colors.WARNING}[!] Restarting wizard untuk memuat library baru...{Colors.ENDC}")
    os.execv(sys.executable, ['python'] + sys.argv)

# --- STEP 2: SETUP DATA FOLDERS ---
def setup_folders():
    print(f"\n{Colors.BLUE}[*] Membuat struktur folder...{Colors.ENDC}")
    folders = [
        "data", "data/scraped", "logs", "sessions", 
        "sessions/devices", "core", "features"
    ]
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    # Create .env if not exists
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write("# Environment Variables\nIG_PASSWORD=\n")
        print(f"{Colors.GREEN}[+] .env file dibuat.{Colors.ENDC}")
    else:
        print(f"{Colors.GREEN}[+] Struktur folder aman.{Colors.ENDC}")

# --- STEP 3: ACCOUNT MANAGEMENT ---
def manage_accounts():
    am = AccountManager()
    
    while True:
        print(f"\n{Colors.CYAN}--- MANAJEMEN AKUN ---{Colors.ENDC}")
        print("1. Tambah Akun Baru")
        print("2. Lihat Daftar Akun")
        print("3. Hapus Akun")
        print("4. Lanjut ke Test Login >>")
        print("0. Keluar")
        
        choice = input(f"{Colors.BOLD}Pilihan: {Colors.ENDC}")
        
        if choice == "1":
            print(f"\n{Colors.YELLOW}Masukkan kredensial akun Instagram:{Colors.ENDC}")
            username = input("Username: ").strip()
            if not username: continue
            
            password = getpass.getpass("Password (hidden): ").strip()
            note = input("Catatan (opsional): ").strip()
            
            spinner("Mengenkripsi data")
            am.add_account(username, password, note)
            print(f"{Colors.GREEN}[+] Akun @{username} berhasil disimpan aman!{Colors.ENDC}")
            
        elif choice == "2":
            am.list_accounts_safe()
            
        elif choice == "3":
            username = input("Username yg akan dihapus: ")
            am.remove_account(username)
            
        elif choice == "4":
            accounts = am.get_accounts()
            if not accounts:
                print(f"{Colors.FAIL}[!] Belum ada akun! Tambahkan dulu.{Colors.ENDC}")
            else:
                break
        
        elif choice == "0":
            sys.exit()
            
        else:
            print("Pilihan salah.")

# --- STEP 4: LOGIN TEST ---
def test_login_sequence():
    print(f"\n{Colors.CYAN}--- PENGUJIAN LOGIN (SMOKE TEST) ---{Colors.ENDC}")
    print(f"{Colors.WARNING}⚠️  Bot akan mencoba login untuk membuat Device ID Indonesia & Session.{Colors.ENDC}")
    
    confirm = input("Lanjut? (y/n): ").lower()
    if confirm != 'y':
        return

    lm = LoginManager()
    accounts = lm.account_manager.get_accounts()
    
    for acc in accounts:
        username = acc['username']
        password = acc['password']
        
        print(f"\n{Colors.BLUE}[*] Mencoba login: @{username}{Colors.ENDC}")
        spinner("Menyiapkan Device ID & Session", duration=1)
        
        try:
            # Login Manager kita sudah otomatis handle Device ID generation
            client = lm.login(username, password)
            
            if client:
                print(f"{Colors.GREEN}[SUCCESS] Login Berhasil!{Colors.ENDC}")
                # Menggunakan .get() agar tidak error jika key tidak ditemukan
                device_model = client.device_settings.get('model', 'Unknown Android')
                locale = client.device_settings.get('locale', 'id_ID')
                
                print(f"   ├─ Device: {device_model}")
                print(f"   ├─ Locale: {locale}")
                print(f"   └─ Status: Session tersimpan di /sessions")
            else:
                print(f"{Colors.FAIL}[FAILED] Gagal login. Cek password atau 2FA.{Colors.ENDC}")
                
        except Exception as e:
            print(f"{Colors.FAIL}[ERROR] {str(e)}{Colors.ENDC}")
            
    print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 SETUP SELESAI! 🎉{Colors.ENDC}")
    print(f"Sekarang jalankan bot utama dengan perintah: {Colors.CYAN}python main.py{Colors.ENDC}")

# --- MAIN ---
if __name__ == "__main__":
    try:
        print_banner()
        check_dependencies()
        setup_folders()
        manage_accounts()
        test_login_sequence()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Setup dibatalkan pengguna.{Colors.ENDC}")