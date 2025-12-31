import sys
import os
import time
import random
import threading
import json
from datetime import datetime, timedelta
import schedule  # Tambahan untuk scheduled post simple
from dotenv import load_dotenv

# Load environment variables dari file .env
load_dotenv()

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

# ================= KONFIGURASI (DIPERBAIKI - PAKAI ENV) =================
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Validasi config
if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("⚠️  WARNING: Telegram credentials belum diset!")
    print("Buat file .env dengan isi:")
    print("  TELEGRAM_TOKEN=token_bot_anda")
    print("  TELEGRAM_CHAT_ID=chat_id_anda")
    print("")

# Inisialisasi
console = Console()
bot_tele = telebot.TeleBot(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None

# Global Variables
active_client = None
current_user_data = None
monitoring_thread = None
last_follower_count = None
scheduler_thread = None

# ================= HELPER FUNCTIONS =================
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def send_telegram_log(message):
    """Kirim log ke telegram tanpa bikin bot macet (Thread)"""
    if not bot_tele or not TELEGRAM_CHAT_ID:
        return  # Skip jika telegram tidak dikonfigurasi
    
    def _send():
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_msg = f"🤖 **BOT REPORT** [{timestamp}]\n\n{message}"
            bot_tele.send_message(TELEGRAM_CHAT_ID, formatted_msg)
        except Exception as e:
            console.print(f"[dim]Telegram log gagal: {e}[/dim]")

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
            "[bold cyan]🔥 INSTAGRAM SAAS DASHBOARD v3.0[/bold cyan]\n"
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
            info = active_client.user_info_v1(my_id)

            show_header()
            console.print(f"\n[bold yellow]👤 DASHBOARD AKUN: @{info.username}[/bold yellow]\n")

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
            medias = active_client.hashtag_medias_v1(hashtag, amount=limit, tab_key="recent")
            if not medias:
                progress.update(task_id, description="[yellow]Switch ke Top Posts...[/yellow]")
                medias = active_client.hashtag_medias_v1(hashtag, amount=limit, tab_key="top")

            if not medias:
                console.print("[red]❌ Tidak ada postingan ditemukan![/red]")
                return

            progress.update(task_id, description="Liking...", total=len(medias))

            for media in medias:
                try:
                    time.sleep(random.uniform(2, 5))
                    active_client.media_like(media.id)
                    sukses += 1
                    progress.update(task_id, advance=1, ok=sukses)
                    time.sleep(random.uniform(3, 8))

                except Exception as e:
                    gagal += 1
                    if "feedback_required" in str(e).lower():
                        console.print("[bold red]⚠️ TERDETEKSI SOFTBAN! Berhenti...[/bold red]")
                        break

        except Exception as e:
            console.print(f"[red]Error System: {e}[/red]")

    laporan = (
        f"✅ **HASIL AUTO LIKE**\n"
        f"Akun: {current_user_data['username']}\n"
        f"Target: #{hashtag}\n"
        f"Sukses: {sukses}\n"
        f"Gagal: {gagal}"
    )
    console.print(Panel(laporan, style="green" if sukses > 0 else "red"))
    send_telegram_log(laporan)
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
                    time.sleep(random.uniform(5, 12))
                except Exception as e:
                    pass

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    laporan = f"✅ **HASIL AUTO FOLLOW**\nAkun: {current_user_data['username']}\nSource: @{target}\nSukses: {sukses}"
    console.print(Panel(laporan, style="blue"))
    send_telegram_log(laporan)
    questionary.press_any_key_to_continue().ask()

def feature_auto_unfollow():
    """Auto unfollow massal"""
    if not active_client: return

    console.print("\n[bold cyan]👥 AUTO UNFOLLOW MANAGER[/bold cyan]")
    limit = int(questionary.text("Jumlah Unfollow:", default="10").ask())

    sukses = 0

    with Progress(
        SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
        TextColumn("{task.completed}/{task.total}"), console=console
    ) as progress:

        task = progress.add_task("Mengambil list following...", total=limit)

        try:
            my_id = active_client.user_id
            following = active_client.user_following(my_id, amount=limit)

            progress.update(task, description="Unfollowing...", total=len(following))

            for uid in following:
                try:
                    active_client.user_unfollow(uid)
                    sukses += 1
                    progress.advance(task)
                    time.sleep(random.uniform(5, 12))  # Delay anti-ban
                except Exception as e:
                    pass

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    laporan = f"✅ **HASIL AUTO UNFOLLOW**\nAkun: {current_user_data['username']}\nSukses: {sukses}"
    console.print(Panel(laporan, style="blue"))
    send_telegram_log(laporan)
    questionary.press_any_key_to_continue().ask()

def feature_auto_comment():
    """Fitur baru: Auto comment massal mirip auto like"""
    if not active_client: return

    console.print("\n[bold cyan]💬 AUTO COMMENT MANAGER[/bold cyan]")
    hashtag = questionary.text("Target Hashtag (tanpa #):").ask()
    if not hashtag: return

    limit = int(questionary.text("Jumlah Comment:", default="10").ask())
    comments = questionary.text("Daftar comment (pisah koma):", default="Nice!,Cool post,Love it").ask().split(',')

    sukses = 0
    gagal = 0

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
            medias = active_client.hashtag_medias_v1(hashtag, amount=limit, tab_key="recent")
            if not medias:
                medias = active_client.hashtag_medias_v1(hashtag, amount=limit, tab_key="top")

            if not medias:
                console.print("[red]❌ Tidak ada postingan ditemukan![/red]")
                return

            progress.update(task_id, description="Commenting...", total=len(medias))

            for media in medias:
                try:
                    comment_text = random.choice(comments).strip()
                    time.sleep(random.uniform(2, 5))
                    active_client.media_comment(media.id, comment_text)
                    sukses += 1
                    progress.update(task_id, advance=1, ok=sukses)
                    time.sleep(random.uniform(3, 8))
                except Exception as e:
                    gagal += 1
                    if "feedback_required" in str(e).lower():
                        console.print("[bold red]⚠️ TERDETEKSI SOFTBAN! Berhenti...[/bold red]")
                        break

        except Exception as e:
            console.print(f"[red]Error System: {e}[/red]")

    laporan = (
        f"✅ **HASIL AUTO COMMENT**\n"
        f"Akun: {current_user_data['username']}\n"
        f"Target: #{hashtag}\n"
        f"Sukses: {sukses}\n"
        f"Gagal: {gagal}"
    )
    console.print(Panel(laporan, style="green" if sukses > 0 else "red"))
    send_telegram_log(laporan)
    questionary.press_any_key_to_continue().ask()

def feature_auto_story_viewer():
    """Fitur baru: Auto view stories massal untuk engagement"""
    if not active_client: return

    console.print("\n[bold cyan]📸 AUTO STORY VIEWER[/bold cyan]")
    target = questionary.text("Username Target (View stories follower dia):").ask()
    if not target: return
    limit = int(questionary.text("Jumlah Stories View:", default="10").ask())

    sukses = 0

    with Progress(
        SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
        TextColumn("{task.completed}/{task.total}"), console=console
    ) as progress:

        task = progress.add_task(f"Mengambil stories dari @{target}...", total=limit)

        try:
            target_id = active_client.user_id_from_username(target)
            stories = active_client.user_stories(target_id, amount=limit)

            progress.update(task, description="Viewing stories...", total=len(stories))

            for story in stories:
                try:
                    active_client.story_seen([story.pk])
                    sukses += 1
                    progress.advance(task)
                    time.sleep(random.uniform(2, 5))  # Delay anti-ban
                except Exception as e:
                    pass

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")

    laporan = f"✅ **HASIL AUTO STORY VIEW**\nAkun: {current_user_data['username']}\nSource: @{target}\nSukses: {sukses}"
    console.print(Panel(laporan, style="blue"))
    send_telegram_log(laporan)
    questionary.press_any_key_to_continue().ask()

def feature_monitor_followers():
    """Monitoring followers real-time via Telegram"""
    global monitoring_thread, last_follower_count
    
    if not active_client: return

    if monitoring_thread and monitoring_thread.is_alive():
        console.print("[yellow]Monitoring sudah berjalan! Tekan Ctrl+C untuk stop.[/yellow]")
        return

    console.print("\n[bold cyan]📊 FOLLOWERS MONITOR[/bold cyan]")
    interval = int(questionary.text("Interval cek (detik):", default="60").ask())

    def monitor_loop():
        global last_follower_count
        try:
            info = active_client.user_info(active_client.user_id)
            last_follower_count = info.follower_count
            console.print(f"[green]Monitoring dimulai. Followers awal: {last_follower_count:,}[/green]")
            
            while True:
                time.sleep(interval)
                info = active_client.user_info(active_client.user_id)
                current_count = info.follower_count
                
                if current_count != last_follower_count:
                    change = current_count - last_follower_count
                    msg = f"📈 **FOLLOWERS UPDATE**\nAkun: {current_user_data['username']}\nPerubahan: {'+' if change > 0 else ''}{change}\nTotal sekarang: {current_count:,}"
                    send_telegram_log(msg)
                    console.print(f"[yellow]{msg}[/yellow]")
                    last_follower_count = current_count
        except Exception as e:
            console.print(f"[red]Monitoring error: {e}. Restart fitur.[/red]")

    monitoring_thread = threading.Thread(target=monitor_loop)
    monitoring_thread.daemon = True
    monitoring_thread.start()
    
    console.print("[dim]Monitoring berjalan di background. Kembali ke menu...[/dim]")
    questionary.press_any_key_to_continue().ask()

def feature_scheduled_post():
    """Fitur scheduled post simple: Set jadwal via menu, run background tanpa cron"""
    global scheduler_thread
    
    if not active_client: return

    if scheduler_thread and scheduler_thread.is_alive():
        console.print("[yellow]Scheduler sudah berjalan! Untuk stop, restart bot.[/yellow]")
        return

    console.print("\n[bold cyan]📅 SCHEDULED POST MANAGER[/bold cyan]")
    console.print("[dim]Set jadwal post otomatis (foto random dari folder 'photos', caption random).[/dim]")

    photo_dir = "photos"  # Folder foto
    if not os.path.exists(photo_dir):
        os.makedirs(photo_dir)
        console.print("[yellow]Folder 'photos' dibuat. Tambah foto JPG/PNG di sana.[/yellow]")

    captions = questionary.text("Daftar caption (pisah koma):", default="Hello world!,Good day,Insta post").ask().split(',')
    interval = questionary.select(
        "Jadwal post:",
        choices=["Setiap jam", "Setiap hari", "Setiap minggu", "Custom (menit)"]
    ).ask()

    if interval == "Custom (menit)":
        minutes = int(questionary.text("Setiap berapa menit:", default="60").ask())
        schedule_interval = lambda: schedule.every(minutes).minutes.do(post_job)
    elif interval == "Setiap jam":
        schedule_interval = lambda: schedule.every().hour.do(post_job)
    elif interval == "Setiap hari":
        schedule_interval = lambda: schedule.every().day.do(post_job)
    elif interval == "Setiap minggu":
        schedule_interval = lambda: schedule.every().week.do(post_job)

    def post_job():
        try:
            photos = [f for f in os.listdir(photo_dir) if f.lower().endswith(('.jpg', '.png'))]
            if not photos:
                send_telegram_log("❌ No photos in folder for scheduled post!")
                return
            photo_path = os.path.join(photo_dir, random.choice(photos))
            caption = random.choice(captions).strip()
            active_client.photo_upload(photo_path, caption=caption)
            msg = f"📸 **SCHEDULED POST SUKSES**\nAkun: {current_user_data['username']}\nCaption: {caption}"
            send_telegram_log(msg)
            console.print(f"[green]{msg}[/green]")
        except Exception as e:
            send_telegram_log(f"❌ Scheduled post error: {str(e)}")

    def scheduler_loop():
        schedule_interval()
        while True:
            schedule.run_pending()
            time.sleep(1)

    scheduler_thread = threading.Thread(target=scheduler_loop)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    console.print("[green]Scheduled post dimulai di background! Cek Telegram untuk notif.[/green]")
    questionary.press_any_key_to_continue().ask()

# ================= LOGIN SYSTEM =================

def login_menu():
    global active_client, current_user_data

    show_header()

    acc_manager = AccountManager()
    accounts = acc_manager.get_all_accounts()

    if not accounts:
        console.print("[red]❌ Belum ada akun di data/accounts.json[/red]")
        console.print("Silakan tambahkan akun lewat script main.py lu dulu, atau tambah manual.")
        questionary.press_any_key_to_continue().ask()
        return

    choices = [f"{acc['username']}" for acc in accounts]
    choices.append("❌ Kembali")

    choice = questionary.select(
        "Pilih Akun untuk Login:",
        choices=choices,
        style=questionary.Style([('qmark', 'fg:#673ab7 bold'), ('pointer', 'fg:#673ab7 bold')])
    ).ask()

    if choice == "❌ Kembali": return

    selected_acc = next((a for a in accounts if a['username'] == choice), None)
    current_user_data = selected_acc

    lm = LoginManager()

    with console.status(f"[bold green]Sedang login @{selected_acc['username']} dengan Device Spoofing...[/bold green]"):
        try:
            client, success = lm.login_account(selected_acc['username'], selected_acc['password'])

            if success and client:
                active_client = client
                console.print(f"[bold green]✅ Login Berhasil![/bold green]")

                dev_model = client.device_settings.get('model', 'Unknown')
                console.print(f"[dim]Connected via: {dev_model}[/dim]")

                send_telegram_log(f"🔓 **LOGIN ALERT**\nUser: {selected_acc['username']}\nStatus: Online\nDevice: 