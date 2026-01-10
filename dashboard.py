import sys
import os
import time
import random
import threading
import json
from datetime import datetime

# Import Library
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.align import Align
from rich import print as rprint
import questionary
import telebot

# =================================================================
# ⚠️⚠️⚠️ CONFIG TELEGRAM (ISI ULANG PUNYA LU DISINI) ⚠️⚠️⚠️
# =================================================================

TELEGRAM_TOKEN   = '8013913254:AAEgPHrPD2_qzr2K0mtphdQlG5C-rZfth28'   # <--- PASTE TOKEN DISINI
TELEGRAM_CHAT_ID = '551845725' # <--- PASTE ID DISINI

# =================================================================

# --- INTEGRASI CORE ---
sys.path.append(os.getcwd())

try:
    from core.account_manager import AccountManager
    from core.login_manager import LoginManager
except ImportError:
    pass

# Inisialisasi
console = Console()
# Cek token sederhana
if 'MASUKKAN_TOKEN' in TELEGRAM_TOKEN:
    console.print("[bold red]❌ ERROR: TOKEN BELUM DIISI![/bold red]")
    console.print("Edit baris 20 di file dashboard.py dulu bos.")
    sys.exit()

bot_tele = telebot.TeleBot(TELEGRAM_TOKEN)

# Global Variables
active_client = None
current_user_data = None

# ================= HELPER FUNCTIONS =================
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def format_indo(angka):
    try:
        return f"{int(angka):,}".replace(",", ".")
    except:
        return str(angka)

def send_telegram_log(message):
    def _send():
        try:
            timestamp = datetime.now().strftime("%H:%M")
            formatted_msg = f"🤖 **BOT REPORT** [{timestamp}]\n\n{message}"
            bot_tele.send_message(TELEGRAM_CHAT_ID, formatted_msg)
        except: pass
    t = threading.Thread(target=_send)
    t.daemon = True
    t.start()

def show_header():
    clear()
    console.print(
        Panel(
            Align.center(
                "[bold cyan]🔥 INSTAGRAM COMMAND CENTER 🔥[/bold cyan]\n"
                "[dim]V4.0 • Auto Add Account • Fix Login[/dim]"
            ),
            style="bold blue",
            border_style="blue"
        )
    )

# ================= FITUR UTAMA =================

def info_dashboard():
    if not active_client: return
    with console.status("[bold green]Mengambil data akun...[/bold green]"):
        try:
            my_id = active_client.user_id
            info = active_client.user_info_v1(my_id)
            show_header()
            
            table = Table(title=f"PROFIL: @{info.username}", title_style="bold yellow", expand=True)
            table.add_column("METRIK", justify="right", style="cyan", no_wrap=True)
            table.add_column("NILAI", style="magenta bold")
            table.add_row("Nama", info.full_name)
            table.add_row("Followers", format_indo(info.follower_count))
            table.add_row("Following", format_indo(info.following_count))
            table.add_row("Total Post", format_indo(info.media_count))
            
            console.print(table)
            dev = active_client.device_settings
            dev_info = f"📱 Device: [white]{dev['model']}[/white] | 🆔 Android ID: [white]{active_client.android_device_id[:16]}...[/white]"
            console.print(Panel(dev_info, title="Security Layer", style="green"))
            questionary.press_any_key_to_continue().ask()
        except Exception as e:
            console.print(f"[bold red]❌ Gagal: {e}[/bold red]")
            questionary.press_any_key_to_continue().ask()

def feature_auto_like():
    if not active_client: return
    console.print("\n[bold cyan]❤️ AUTO LIKE ENGINE[/bold cyan]")
    hashtag = questionary.text("Target Hashtag (tanpa #):").ask()
    if not hashtag: return
    limit = int(questionary.text("Jumlah Like:", default="10").ask())
    
    sukses, gagal = 0, 0
    with Progress(
        SpinnerColumn(), TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None, style="dim", complete_style="green"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"), console=console
    ) as progress:
        task_id = progress.add_task("Mencari Target...", total=limit)
        try:
            medias = active_client.hashtag_medias_v1(hashtag, amount=limit, tab_key="recent")
            if not medias:
                progress.update(task_id, description="[yellow]Mode Top Posts...[/yellow]")
                medias = active_client.hashtag_medias_v1(hashtag, amount=limit, tab_key="top")
            
            if not medias:
                console.print("[red]❌ Zonk! Tidak ada postingan.[/red]")
                time.sleep(2)
                return

            progress.update(task_id, description="Processing...", total=len(medias))
            for media in medias:
                try:
                    time.sleep(random.uniform(2, 4))
                    active_client.media_like(media.id)
                    sukses += 1
                    progress.console.print(f"   ✅ Liked: [white]{media.code}[/white]")
                    progress.advance(task_id)
                    time.sleep(random.uniform(3, 7))
                except Exception as e:
                    gagal += 1
                    if "feedback_required" in str(e).lower():
                        progress.console.print("[bold red]⚠️ SOFTBAN DETECTED![/bold red]")
                        break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            
    report = f"✅ **AUTO LIKE SELESAI**\nUser: {current_user_data['username']}\nTarget: #{hashtag}\nSukses: {sukses} | Gagal: {gagal}"
    send_telegram_log(report)
    console.print(Panel(f"Sukses: {sukses} | Gagal: {gagal}", title="Hasil", style="green"))
    questionary.press_any_key_to_continue().ask()

def feature_auto_follow():
    if not active_client: return
    console.print("\n[bold cyan]👥 AUTO FOLLOW ENGINE[/bold cyan]")
    target = questionary.text("Target Username:").ask()
    if not target: return
    limit = int(questionary.text("Jumlah Follow:", default="10").ask())
    sukses = 0
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), console=console) as progress:
        task = progress.add_task("Scraping...", total=limit)
        try:
            target_id = active_client.user_id_from_username(target)
            followers = active_client.user_followers(target_id, amount=limit)
            progress.update(task, description="Following...", total=len(followers))
            for uid in followers:
                try:
                    active_client.user_follow(uid)
                    sukses += 1
                    progress.console.print(f"   ➕ Followed: {uid}")
                    progress.advance(task)
                    time.sleep(random.uniform(4, 9))
                except: pass
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    send_telegram_log(f"✅ **AUTO FOLLOW SELESAI**\nUser: {current_user_data['username']}\nTarget: @{target}\nSukses: {sukses}")
    questionary.press_any_key_to_continue().ask()

# ================= LOGIN SYSTEM =================

def login_menu():
    global active_client, current_user_data
    show_header()
    
    try:
        acc_manager = AccountManager()
        accounts = acc_manager.get_all_accounts()
    except:
        console.print("[red]❌ Gagal memuat database akun![/red]")
        return

    # --- FITUR BARU: AUTO ADD ACCOUNT ---
    choices = []
    if accounts:
        choices = [f"{acc['username']}" for acc in accounts]
    
    choices.insert(0, "➕ Tambah Akun Baru") # Menu baru
    choices.append("❌ Kembali")
    
    choice = questionary.select("Pilih Akun:", choices=choices).ask()
    
    if choice == "❌ Kembali": 
        return
        
    elif choice == "➕ Tambah Akun Baru":
        console.print("\n[bold yellow]📝 INPUT DATA AKUN BARU[/bold yellow]")
        new_user = questionary.text("Username Instagram:").ask()
        new_pass = questionary.password("Password Instagram:").ask()
        
        if new_user and new_pass:
            acc_manager.add_account(new_user, new_pass)
            console.print(f"[bold green]✅ Akun {new_user} berhasil disimpan![/bold green]")
            time.sleep(1)
            login_menu() # Refresh menu biar akunnya muncul
        return

    # Login Process
    selected_acc = next((a for a in accounts if a['username'] == choice), None)
    if not selected_acc: return
    
    current_user_data = selected_acc
    lm = LoginManager()
    
    with console.status(f"[bold green]Login @{choice}...[/bold green]"):
        try:
            client, success = lm.login_account(selected_acc['username'], selected_acc['password'])
            if success:
                active_client = client
                send_telegram_log(f"🔓 **LOGIN SUKSES**\nUser: {choice}\nDevice: {client.device_settings['model']}")
            else:
                console.print("[red]❌ Password Salah / Kena Checkpoint[/red]")
                questionary.press_any_key_to_continue().ask()
        except Exception as e:
             console.print(f"[red]❌ Error Login: {e}[/red]")
             questionary.press_any_key_to_continue().ask()

# ================= MAIN MENU =================

def main():
    global active_client, current_user_data # FIX UNBOUND LOCAL ERROR
    
    while True:
        show_header()
        
        if active_client:
            status = f"[bold green]● ONLINE: @{current_user_data['username']}[/bold green]"
            menu = ["👤 Dashboard", "❤️ Auto Like", "👥 Auto Follow", "🚪 Logout", "❌ Exit"]
        else:
            status = "[bold red]○ OFFLINE[/bold red]"
            menu = ["🔐 Login Akun", "❌ Exit"]
            
        console.print(Panel(Align.center(status), style="white"))
        
        choice = questionary.select("MENU UTAMA", choices=menu).ask()
        
        if choice == "🔐 Login Akun": login_menu()
        elif choice == "👤 Dashboard": info_dashboard()
        elif choice == "❤️ Auto Like": feature_auto_like()
        elif choice == "👥 Auto Follow": feature_auto_follow()
        elif choice == "🚪 Logout": 
            active_client = None
            current_user_data = None
        elif choice == "❌ Exit": break

if __name__ == "__main__":
    main()