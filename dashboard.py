import sys
import os
import time
import random
import threading
import json
from datetime import datetime

# Import Library UI Keren
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
import questionary

# Import Telegram
import telebot

# --- INTEGRASI DENGAN KODE CORE LU ---
# Kita tambahin path biar bisa import folder 'core'
sys.path.append(os.getcwd())

try:
    from core.account_manager import AccountManager
    from core.login_manager import LoginManager
    from instagrapi.exceptions import (
        BadPassword, TwoFactorRequired, ChallengeRequired, 
        FeedbackRequired, LoginRequired
    )
except ImportError as e:
    print("❌ ERROR STRUKTUR FILE:")
    print("Pastikan file ini (dashboard.py) ada di folder yang sama dengan folder 'core/'")
    print(f"Detail: {e}")
    sys.exit()

# ================= KONFIGURASI =================
TELEGRAM_TOKEN = 'MASUKKAN_TOKEN_BOT_LU_DISINI'
TELEGRAM_CHAT_ID = 'MASUKKAN_ID_TELEGRAM_LU_DISINI'

# Inisialisasi
console = Console()
bot_tele = telebot.TeleBot(TELEGRAM_TOKEN)

# Global Variables
active_client = None
current_user_data = None

# ================= HELPER FUNCTIONS =================
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def send_telegram_log(message):
    """Kirim log ke telegram tanpa bikin bot macet (Thread)"""
    def _send():
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_msg = f"🤖 **BOT REPORT** [{timestamp}]\n\n{message}"
            bot_tele.send_message(TELEGRAM_CHAT_ID, formatted_msg)
        except: pass
    
    # Jalankan di background
    t = threading.Thread(target=_send)
    t.daemon = True
    t.start()

def show_header():
    clear()
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_row(
        Panel(
            "[bold cyan]🔥 INSTAGRAM SAAS DASHBOARD v2.0[/bold cyan]\n"
            "[white]Control Center • Device Faker • Smart Automation[/white]",
            style="bold blue",
            subtitle="Created by Lu Sendiri"
        )
    )
    console.print(grid)

# ================= FITUR UTAMA =================

def info_dashboard():
    """Menampilkan Info Akun dalam bentuk Tabel Cantik"""
    if not active_client: return
    
    with console.status("[bold green]Mengambil data terbaru dari server IG...[/bold green]"):
        try:
            my_id = active_client.user_id
            # Pake v1 biar aman dari limit web
            info = active_client.user_info_v1(my_id)
            
            show_header()
            console.print(f"\n[bold yellow]👤 DASHBOARD AKUN: @{info.username}[/bold yellow]\n")
            
            # Tabel Utama
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="white bold")
            
            table.add_row("Nama Lengkap", info.full_name)
            table.add_row("Followers", f"{info.follower_count:,}")
            table.add_row("Following", f"{info.following_count:,}")
            table.add_row("Total Post", f"{info.media_count}")
            table.add_row("Akun Private?", "🔒 Ya" if info.is_private else "🌍 Tidak")
            table.add_row("Business Acc?", "🏢 Ya" if info.is_business else "👤 Tidak")
            
            console.print(table)
            
            # Tampilkan Info Device (Dari LoginManager lu)
            dev = active_client.device_settings
            console.print(Panel(
                f"📱 [bold]Device Identity:[/bold] {dev['model']} ({dev['manufacturer']})\n"
                f"🆔 [bold]Android ID:[/bold] {active_client.android_device_id}",
                title="Security Info", style="green"
            ))
            
            questionary.press_any_key_to_continue().ask()
            
        except Exception as e:
            console.print(f"[bold red]❌ Gagal ambil info: {e}[/bold red]")
            questionary.press_any_key_to_continue().ask()

def feature_auto_like():
    if not active_client: return
    
    console.print("\n[bold cyan]❤️ AUTO LIKE MANAGER[/bold cyan]")
    hashtag = questionary.text("Target Hashtag (tanpa #):").ask()
    if not hashtag: return
    
    limit = int(questionary.text("Jumlah Like:", default="10").ask())
    
    console.print(f"[dim]Memulai engine... Target: #{hashtag}[/dim]")
    
    sukses = 0
    gagal = 0
    
    # Progress Bar UI
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        "•",
        TextColumn("[green]Sukses: {task.fields[ok]}[/green]"),
        console=console
    ) as progress:
        
        task_id = progress.add_task("Mencari Target...", total=limit, ok=0)
        
        try:
            # 1. Cari Media (Pake Smart Fallback)
            medias = active_client.hashtag_medias_v1(hashtag, amount=limit, tab_key="recent")
            if not medias:
                progress.update(task_id, description="[yellow]Switch ke Top Posts...[/yellow]")
                medias = active_client.hashtag_medias_v1(hashtag, amount=limit, tab_key="top")
            
            if not medias:
                console.print("[red]❌ Tidak ada postingan ditemukan![/red]")
                return

            # 2. Eksekusi
            progress.update(task_id, description="Liking...", total=len(medias))
            
            for media in medias:
                try:
                    # Simulasi Human Delay
                    time.sleep(random.uniform(2, 5))
                    
                    active_client.media_like(media.id)
                    sukses += 1
                    progress.update(task_id, advance=1, ok=sukses)
                    
                    # Jeda antar like
                    time.sleep(random.uniform(3, 8))
                    
                except Exception as e:
                    gagal += 1
                    # Cek softban
                    if "feedback_required" in str(e).lower():
                        console.print("[bold red]⚠️ TERDETEKSI SOFTBAN! Berhenti...[/bold red]")
                        break
        
        except Exception as e:
            console.print(f"[red]Error System: {e}[/red]")
            
    # Report Akhir
    laporan = (
        f"✅ **HASIL AUTO LIKE**\n"
        f"Akun: {current_user_data['username']}\n"
        f"Target: #{hashtag}\n"
        f"Sukses: {sukses}\n"
        f"Gagal: {gagal}"
    )
    console.print(Panel(laporan, style="green" if sukses > 0 else "red"))
    send_telegram_log(laporan) # Kirim ke Telegram
    questionary.press_any_key_to_continue().ask()

def feature_auto_follow():
    if not active_client: return
    
    console.print("\n[bold cyan]👥 AUTO FOLLOW MANAGER[/bold cyan]")
    target = questionary.text("Username Target (Ambil follower dia):").ask()
    if not target: return
    limit = int(questionary.text("Jumlah Follow:", default="10").ask())
    
    sukses = 0
    
    with Progress(
        SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), 
        TextColumn("{task.completed}/{task.total}"), console=console
    ) as progress:
        
        task = progress.add_task(f"Mengambil data @{target}...", total=limit)
        
        try:
            target_id = active_client.user_id_from_username(target)
            followers = active_client.user_followers(target_id, amount=limit)
            
            progress.update(task, description="Following...", total=len(followers))
            
            for uid in followers:
                try:
                    active_client.user_follow(uid)
                    sukses += 1
                    progress.advance(task)
                    time.sleep(random.uniform(5, 12)) # Delay aman
                except Exception as e:
                    pass
                    
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            
    laporan = f"✅ **HASIL AUTO FOLLOW**\nAkun: {current_user_data['username']}\nSource: @{target}\nSukses: {sukses}"
    console.print(Panel(laporan, style="blue"))
    send_telegram_log(laporan)
    questionary.press_any_key_to_continue().ask()

# ================= LOGIN SYSTEM =================

def login_menu():
    global active_client, current_user_data
    
    show_header()
    
    # 1. Load Akun dari Database JSON lu
    acc_manager = AccountManager()
    accounts = acc_manager.get_all_accounts() # Fungsi ini ada di core/account_manager.py lu
    
    if not accounts:
        console.print("[red]❌ Belum ada akun di data/accounts.json[/red]")
        console.print("Silakan tambahkan akun lewat script main.py lu dulu, atau tambah manual.")
        questionary.press_any_key_to_continue().ask()
        return

    # 2. Bikin Menu Pilihan Akun
    # Format: "username (nama)"
    choices = [f"{acc['username']}" for acc in accounts]
    choices.append("❌ Kembali")
    
    choice = questionary.select(
        "Pilih Akun untuk Login:",
        choices=choices,
        style=questionary.Style([('qmark', 'fg:#673ab7 bold'), ('pointer', 'fg:#673ab7 bold')])
    ).ask()
    
    if choice == "❌ Kembali": return
    
    # Ambil data akun yang dipilih
    selected_acc = next((a for a in accounts if a['username'] == choice), None)
    current_user_data = selected_acc
    
    # 3. Proses Login
    lm = LoginManager() # Pake class LoginManager canggih lu
    
    with console.status(f"[bold green]Sedang login @{selected_acc['username']} dengan Device Spoofing...[/bold green]"):
        try:
            # LoginManager lu nge-return (client, status)
            # Kita panggil fungsi login_account(username, password)
            client, success = lm.login_account(selected_acc['username'], selected_acc['password'])
            
            if success and client:
                active_client = client
                console.print(f"[bold green]✅ Login Berhasil![/bold green]")
                
                # Cek session validitas
                dev_model = client.device_settings.get('model', 'Unknown')
                console.print(f"[dim]Connected via: {dev_model}[/dim]")
                
                send_telegram_log(f"🔓 **LOGIN ALERT**\nUser: {selected_acc['username']}\nStatus: Online\nDevice: {dev_model}")
                time.sleep(2)
            else:
                console.print("[bold red]❌ Login Gagal. Cek password/koneksi.[/bold red]")
                questionary.press_any_key_to_continue().ask()
                
        except TwoFactorRequired:
            console.print("[yellow]⚠️ Masukkan Kode 2FA:[/yellow]")
            code = questionary.text("Code:").ask()
            # Handle 2FA manual disini kalo LoginManager lu ga handle interaktif
            # Tapi asumsi gua LoginManager lu return client objek, kita bisa pake itu
            try:
                # Kita perlu client sementara utk input code, ini agak tricky kalo via Manager
                # Makanya sebaiknya LoginManager lu handle return object client meski 2FA
                pass 
            except:
                pass
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            questionary.press_any_key_to_continue().ask()

# ================= MAIN MENU =================

def main():
    while True:
        show_header()
        
        # Status Bar
        if active_client:
            status = f"[bold green]ONLINE: @{current_user_data['username']}[/bold green]"
            menu_list = [
                "👤 Dashboard Akun",
                "❤️ Auto Like",
                "👥 Auto Follow",
                "🚪 Logout / Ganti Akun",
                "❌ Keluar Aplikasi"
            ]
        else:
            status = "[bold red]OFFLINE (Belum Login)[/bold red]"
            menu_list = [
                "🔐 Login Akun",
                "❌ Keluar Aplikasi"
            ]
            
        console.print(Panel(status, style="white"))
        
        choice = questionary.select(
            "Main Menu:",
            choices=menu_list
        ).ask()
        
        if choice == "🔐 Login Akun":
            login_menu()
        elif choice == "👤 Dashboard Akun":
            info_dashboard()
        elif choice == "❤️ Auto Like":
            feature_auto_like()
        elif choice == "👥 Auto Follow":
            feature_auto_follow()
        elif choice == "🚪 Logout / Ganti Akun":
            active_client = None
            current_user_data = None
            console.print("[yellow]Logged out.[/yellow]")
            time.sleep(1)
        elif choice == "❌ Keluar Aplikasi":
            console.print("Bye bye! 👋")
            break

if __name__ == "__main__":
    main()
