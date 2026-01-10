#!/usr/bin/env python3
"""
Dashboard CLI - V16 (ACTIVITY LOG EDITION)
Fitur:
- Activity Logging (.txt recorder)
- View Log Menu
- Auto Analytics (Real-time Fetch)
- Whitelist Manager
- Auto Unfollow & Search Mode
- Login Select Mode
"""

import os
import sys
import time
import random
import json
from datetime import datetime

# Library UI Modern
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.align import Align
from rich import print as rprint
import questionary

# Import core modules
try:
    from core.login_manager import LoginManager
    from core.account_manager import AccountManager
    from core.scheduler import MultiAccountScheduler
    from core.analytics import Analytics
    from instagrapi.exceptions import UserNotFound, PrivateAccount, FeedbackRequired
except ImportError as e:
    print(f"❌ Error Import: {e}")
    print("Pastikan folder 'core' ada di lokasi yang sama.")
    sys.exit()

class DashboardController:
    def __init__(self):
        self.account_manager = AccountManager()
        self.login_manager = LoginManager()
        self.scheduler = MultiAccountScheduler()
        self.analytics = Analytics()
        
        self.username = None
        self.client = None
        self.console = Console()
        
        # Init Data Folders
        if not os.path.exists("data"): os.makedirs("data")
        
        # Init Whitelist DB
        self.whitelist_path = os.path.join("data", "whitelist.json")
        if not os.path.exists(self.whitelist_path):
            with open(self.whitelist_path, 'w') as f: json.dump([], f)
            
        # Init Log File (Buat file kosong kalau belum ada)
        self.log_path = os.path.join("data", "activity_log.txt")
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w') as f: f.write("=== BOT ACTIVITY LOG ===\n")

    # =====================================================
    # 🎨 HELPER UI & LOGGING SYSTEM
    # =====================================================
    def _clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def _format_indo(self, value):
        try:
            val_fmt = f"{int(value):,}".replace(",", ".")
            return f"[bold cyan]{val_fmt}[/bold cyan]"
        except: return str(value)

    def _log_activity(self, action, details):
        """Mencatat aktivitas ke file txt"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {action}: {details}"
        
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except: pass

    def _banner(self):
        self._clear_screen()
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(
            Panel(
                Align.center(
                    "[bold cyan]🌐 BUCOL INSTAGRAM BOT[/bold cyan]\n"
                    "[dim]v16.0 • Activity Log Recorder • Monitoring System[/dim]"
                ),
                style="bold blue",
                border_style="blue",
            )
        )
        self.console.print(grid)

    def _pause(self):
        self.console.input("\n[dim]Tekan [bold white]Enter[/bold white] untuk kembali...[/dim]")

    def _loading(self, text="Memproses"):
        with self.console.status(f"[bold green]{text}...[/bold green]", spinner="dots"):
            time.sleep(1.0)

    # =====================================================
    # 📜 MENU VIEW LOG (FITUR BARU)
    # =====================================================
    def view_activity_log(self):
        self._banner()
        if not os.path.exists(self.log_path):
            self.console.print("[yellow]⚠️ Belum ada log aktivitas.[/yellow]")
        else:
            self.console.print(Panel("[bold cyan]📜 ACTIVITY LOG (20 Terakhir)[/bold cyan]", expand=False))
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # Ambil 20 baris terakhir biar gak kepenuhan
                    last_lines = lines[-20:] if len(lines) > 20 else lines
                    
                    for line in last_lines:
                        line = line.strip()
                        if not line: continue
                        
                        # Warnai output biar enak dibaca
                        if "LIKED" in line: style = "green"
                        elif "FOLLOWED" in line: style = "blue"
                        elif "UNFOLLOWED" in line: style = "red"
                        else: style = "white"
                        
                        self.console.print(f"[{style}]{line}[/{style}]")
                    
                    self.console.print(f"\n[dim]Total Record: {len(lines)} baris. Cek file data/activity_log.txt untuk log lengkap.[/dim]")
            except Exception as e:
                self.console.print(f"[red]Gagal baca log: {e}[/red]")
        
        self._pause()

    # =====================================================
    # 🛡️ WHITELIST MANAGER
    # =====================================================
    def load_whitelist(self):
        try:
            with open(self.whitelist_path, 'r') as f: return json.load(f)
        except: return []

    def save_whitelist(self, data):
        with open(self.whitelist_path, 'w') as f: json.dump(data, f, indent=4)

    def whitelist_menu(self):
        while True:
            self._banner()
            current_list = self.load_whitelist()
            self.console.print(Panel(f"🛡️ WHITELIST (Daftar Kebal Unfollow)\nTotal: [bold green]{len(current_list)} akun[/bold green]", style="cyan"))
            
            choice = questionary.select(
                "MENU WHITELIST",
                choices=[
                    "➕ Tambah Username ke Whitelist",
                    "🗑️  Hapus Username dari Whitelist",
                    "📋 Lihat Daftar Whitelist",
                    "❌ Kembali"
                ]
            ).ask()

            if choice == "❌ Kembali": break

            if choice == "➕ Tambah Username ke Whitelist":
                u = questionary.text("Username (tanpa @):").ask()
                if u:
                    current_list = self.load_whitelist()
                    if u not in current_list:
                        current_list.append(u)
                        self.save_whitelist(current_list)
                        self.console.print(f"[green]✅ @{u} sekarang AMAN dari unfollow![/green]")
                    else: self.console.print(f"[yellow]⚠️ @{u} sudah ada di whitelist.[/yellow]")
                    time.sleep(1.5)

            elif choice == "🗑️  Hapus Username dari Whitelist":
                if not current_list: self.console.print("[red]Whitelist kosong.[/red]"); time.sleep(1); continue
                u = questionary.select("Pilih akun untuk dihapus:", choices=current_list + ["❌ Batal"]).ask()
                if u != "❌ Batal":
                    current_list.remove(u)
                    self.save_whitelist(current_list)
                    self.console.print(f"[yellow]🗑️ @{u} dihapus dari perlindungan.[/yellow]")
                    time.sleep(1.5)

            elif choice == "📋 Lihat Daftar Whitelist":
                if not current_list: self.console.print("[dim]Belum ada akun di whitelist.[/dim]")
                else:
                    t = Table(title="Daftar Akun Kebal")
                    t.add_column("No", style="dim"); t.add_column("Username", style="green")
                    for idx, user in enumerate(current_list, 1): t.add_row(str(idx), user)
                    self.console.print(t)
                questionary.press_any_key_to_continue().ask()

    # =====================================================
    # 🤖 FITUR OTOMATISASI (DENGAN LOGGER)
    # =====================================================
    def feature_auto_like(self):
        if not self.client: self.console.print("[red]❌ Login dulu bos![/red]"); return
        self.console.print(Panel("[bold cyan]❤️ AUTO LIKE ENGINE[/bold cyan]", expand=False))
        hashtag = questionary.text("Target Hashtag (tanpa #):").ask()
        if not hashtag: return
        try: limit = int(questionary.text("Jumlah Like:", default="10").ask())
        except: limit = 10
        
        sukses, gagal = 0, 0
        with Progress(SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(), console=self.console) as progress:
            task_id = progress.add_task("Mencari Target...", total=limit)
            try:
                medias = self.client.hashtag_medias_v1(hashtag, amount=limit, tab_key="recent")
                if not medias: medias = self.client.hashtag_medias_v1(hashtag, amount=limit, tab_key="top")
                if not medias: self.console.print("[red]❌ Zonk! Tidak ada postingan.[/red]"); return

                progress.update(task_id, description="Processing...", total=len(medias))
                for media in medias:
                    try:
                        time.sleep(random.uniform(3, 6))
                        self.client.media_like(media.id)
                        sukses += 1
                        
                        # --- LOGGING ---
                        self._log_activity("LIKED", f"{media.code} (Tag: #{hashtag})")
                        
                        progress.console.print(f"   ✅ Liked: [dim]{media.code}[/dim]")
                        progress.advance(task_id)
                        time.sleep(random.uniform(3, 8))
                    except Exception as e:
                        gagal += 1
                        if "feedback_required" in str(e).lower(): break
            except Exception as e: self.console.print(f"[red]Error System: {e}[/red]")
        self.console.print(f"\n[green]✅ Selesai! Sukses: {sukses}[/green]"); self._pause()

    def feature_auto_follow(self):
        if not self.client: self.console.print("[red]❌ Login dulu bos![/red]"); return
        self.console.print(Panel("[bold cyan]👥 AUTO FOLLOW (SEARCH MODE)[/bold cyan]", expand=False))
        target_username = questionary.text("Target Username (Source):").ask()
        if not target_username: return
        try: limit = int(questionary.text("Jumlah Follow:", default="10").ask())
        except: limit = 10
        
        sukses = 0
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), console=self.console) as progress:
            task = progress.add_task("Mencari User...", total=limit)
            try:
                progress.update(task, description=f"Searching '{target_username}'...")
                search_results = self.client.search_users(target_username)
                target_user = next((u for u in search_results if u.username == target_username), None)
                if not target_user: self.console.print(f"[bold red]❌ User @{target_username} tidak ditemukan![/bold red]"); return
                if target_user.is_private:
                    try:
                        if not self.client.user_following_status(target_user.pk).following:
                            self.console.print(f"[bold red]❌ @{target_username} DIGEMBOK (PRIVATE)![/bold red]"); return
                    except: pass

                progress.update(task, description=f"Scraping followers @{target_username}...")
                followers = self.client.user_followers(target_user.pk, amount=limit)
                if not followers: self.console.print("[yellow]⚠️ Follower kosong.[/yellow]"); return

                progress.update(task, description="Following...", total=len(followers))
                for uid in followers:
                    user_id = uid.pk if hasattr(uid, 'pk') else uid
                    try:
                        self.client.user_follow(user_id)
                        sukses += 1
                        
                        # --- LOGGING ---
                        self._log_activity("FOLLOWED", f"ID {user_id} (Src: @{target_username})")
                        
                        progress.console.print(f"   ➕ Followed ID: {user_id}")
                        progress.advance(task)
                        time.sleep(random.uniform(5, 12)) 
                    except: pass
            except Exception as e:
                 if "JSONDecodeError" in str(e): self.console.print(f"[bold red]❌ INSTAGRAM LIMIT API.[/bold red]")
                 else: self.console.print(f"[red]Error: {e}[/red]")
        self.console.print(f"\n[green]✅ Selesai! Sukses: {sukses}[/green]"); self._pause()

    def feature_auto_unfollow(self):
        if not self.client: self.console.print("[red]❌ Login dulu bos![/red]"); return
        self.console.print(Panel("[bold cyan]🗑️ AUTO UNFOLLOW (WITH LOGGING)[/bold cyan]", expand=False))
        mode = questionary.select("Pilih Mode Unfollow:", choices=["1. Unfollow Yang Tidak Follback", "2. Unfollow Semua (Kecuali Whitelist)", "❌ Batal"]).ask()
        if mode == "❌ Batal": return
        try: limit = int(questionary.text("Maksimal Unfollow:", default="10").ask())
        except: limit = 10

        self.console.print("\n[yellow]⏳ Analisa data & whitelist...[/yellow]")
        whitelist = self.load_whitelist()
        my_id = self.client.user_id
        targets_to_unfollow = []

        try:
            following_dict = self.client.user_following(my_id)
            if mode.startswith("2"): candidates = list(following_dict.keys())
            else:
                followers_dict = self.client.user_followers(my_id)
                not_follback_set = set(following_dict.keys()) - set(followers_dict.keys())
                candidates = list(not_follback_set)
            
            safe_count = 0
            for uid in candidates:
                user_obj = following_dict.get(uid)
                if user_obj:
                    if user_obj.username in whitelist: safe_count += 1; continue
                    targets_to_unfollow.append(uid)

            self.console.print(f"[bold]Total Kandidat:[/bold] {len(candidates)}")
            self.console.print(f"[bold green]🛡️ Whitelist Safe:[/bold green] {safe_count}")
            self.console.print(f"[bold red]💀 Siap Unfollow:[/bold red] {len(targets_to_unfollow)}")

            if len(targets_to_unfollow) > limit: targets_to_unfollow = targets_to_unfollow[:limit]
            if not targets_to_unfollow: self.console.print("[green]✅ Aman![/green]"); self._pause(); return

            confirm = questionary.confirm(f"Lanjut unfollow {len(targets_to_unfollow)} akun?").ask()
            if not confirm: return

            sukses = 0
            with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), console=self.console) as progress:
                task = progress.add_task("Unfollowing...", total=len(targets_to_unfollow))
                for uid in targets_to_unfollow:
                    try:
                        user_obj = following_dict.get(uid)
                        uname = user_obj.username if user_obj else str(uid)
                        self.client.user_unfollow(uid)
                        sukses += 1
                        
                        # --- LOGGING ---
                        self._log_activity("UNFOLLOWED", f"@{uname}")
                        
                        progress.console.print(f"   🗑️  Bye @{uname}")
                        progress.advance(task)
                        time.sleep(random.uniform(4, 8))
                    except Exception as e: progress.console.print(f"[red]Gagal: {e}[/red]")

            self.console.print(f"\n[green]✅ Selesai! {sukses} akun di-unfollow.[/green]")
        except Exception as e: self.console.print(f"[red]Error: {e}[/red]")
        self._pause()

    def automation_menu(self):
        while True:
            self._banner()
            if not self.client: self.console.print("[bold red]⚠️ BELUM LOGIN.[/bold red] Login dulu di menu utama.")
            choice = questionary.select("🤖 FITUR OTOMATISASI", choices=["❤️ Auto Like (Hashtag)", "👥 Auto Follow (Target User)", "🗑️ Auto Unfollow (Cleaner)", "🛡️ Kelola Whitelist (Anti-Unfollow)", "❌ Kembali"]).ask()
            if choice == "❌ Kembali": break
            if choice == "❤️ Auto Like (Hashtag)": self.feature_auto_like()
            elif choice == "👥 Auto Follow (Target User)": self.feature_auto_follow()
            elif choice == "🗑️ Auto Unfollow (Cleaner)": self.feature_auto_unfollow()
            elif choice == "🛡️ Kelola Whitelist (Anti-Unfollow)": self.whitelist_menu()

    # =====================================================
    # 📊 ANALYTICS
    # =====================================================
    def analytics_menu(self):
        while True:
            self._banner()
            choice = questionary.select("📊 ANALYTICS MENU", choices=["🔄 Sync Data Statistik (Auto Fetch)", "📈 Tampilkan Laporan", "❌ Kembali"]).ask()
            if choice == "❌ Kembali": break
            if choice == "🔄 Sync Data Statistik (Auto Fetch)":
                if not self.client: self.console.print("[red]❌ Login dulu bos![/red]"); self._pause(); continue
                self.console.print("[yellow]⏳ Fetch data server Instagram...[/yellow]")
                try:
                    my_id = self.client.user_id
                    info = self.client.user_info(my_id)
                    self.console.print(Panel(f"[bold]STATUS (@{info.username})[/bold]\n\n👥 Followers : {self._format_indo(info.follower_count)}\n👤 Following : {self._format_indo(info.following_count)}\n📸 Total Post: {self._format_indo(info.media_count)}", title="Live Data", style="cyan"))
                    self.analytics.record_daily_stats(info.username, info.follower_count, info.following_count, info.media_count, 0, 0)
                    self.console.print(f"\n[green]✅ Data tercatat![/green]")
                except Exception as e: self.console.print(f"[red]Gagal: {e}[/red]")
                self._pause()
            elif choice == "📈 Tampilkan Laporan":
                u = questionary.text("Username:").ask()
                if u: print("\n"); self.analytics.print_report(u); print("\n"); questionary.press_any_key_to_continue().ask()

    # =====================================================
    # 🔑 LOGIN & ACCOUNT
    # =====================================================
    def login_menu(self):
        self._banner()
        self.console.print(Panel("[bold green]🔐 LOGIN AREA[/bold green]", expand=False))
        db_path = os.path.join("data", "accounts.json")
        accounts = []
        if os.path.exists(db_path):
            try:
                with open(db_path, 'r') as f:
                    content = f.read().strip()
                    if content: accounts = json.loads(content)
            except: pass
        if not accounts: self.console.print("\n[bold yellow]⚠️  DATABASE KOSONG![/bold yellow]"); self._pause(); return
        choices = [acc['username'] for acc in accounts] + ["❌ Kembali"]
        selected_user = questionary.select("Pilih Akun:", choices=choices).ask()
        if selected_user == "❌ Kembali": return
        target_acc = next((a for a in accounts if a['username'] == selected_user), None)
        self._loading(f"Login ke @{selected_user}")
        try:
            result = self.login_manager.login(selected_user, target_acc['password'])
            if isinstance(result, tuple) and len(result) >= 1:
                is_success = result[0]; self.client = result[2] if len(result) > 2 else result
            else: is_success = True if result else False; self.client = result
            if is_success:
                self.username = selected_user; self.console.print(f"\n[bold green]✅ Login Berhasil![/bold green] Welcome [cyan]@{selected_user}[/cyan]")
            else: self.console.print(f"\n[bold red]❌ Gagal Login.[/bold red]")
        except Exception as e: self.console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        self._pause()

    def account_menu(self):
        while True:
            self._banner()
            choice = questionary.select("👤 KELOLA AKUN", choices=["➕ Tambah Akun Baru", "🗑️  Hapus Akun", "📋 Lihat Daftar Akun", "❌ Kembali"]).ask()
            if choice == "❌ Kembali": break
            if choice == "➕ Tambah Akun Baru":
                u = questionary.text("Username:").ask(); p = questionary.password("Password:").ask()
                if u and p: self.account_manager.add_account(u, p); self.console.print(f"[green]✅ Akun {u} disimpan![/green]"); time.sleep(1)
            elif choice == "🗑️  Hapus Akun":
                u = questionary.text("Username dihapus:").ask()
                if u: self.account_manager.remove_account(u); self.console.print("[yellow]🗑️  Dihapus.[/yellow]"); time.sleep(1)
            elif choice == "📋 Lihat Daftar Akun": print("\n"); self.account_manager.list_accounts(); print("\n"); questionary.press_any_key_to_continue().ask()

    def main_menu(self):
        while True:
            self._banner()
            status_text = f"● ONLINE: @{self.username}" if self.username else "○ OFFLINE"
            status_color = "green" if self.username else "red"
            self.console.print(Align.center(f"[{status_color}]{status_text}[/{status_color}]"))
            self.console.print("")
            choice = questionary.select("MENU UTAMA", choices=["🔐 Login Akun", "🤖 Fitur Bot (Like/Follow/Unfollow)", "📜 Lihat Activity Log", "👤 Kelola Database Akun", "📊 Menu Analytics", "❌ Keluar"]).ask() # <--- MENU LOG ADA DISINI
            if choice == "🔐 Login Akun": self.login_menu()
            elif choice == "🤖 Fitur Bot (Like/Follow/Unfollow)": self.automation_menu()
            elif choice == "📜 Lihat Activity Log": self.view_activity_log()
            elif choice == "👤 Kelola Database Akun": self.account_menu()
            elif choice == "📊 Menu Analytics": self.analytics_menu()
            elif choice == "❌ Keluar": self.console.print("[bold]Bye bye! 👋[/bold]"); break

if __name__ == "__main__":
    try: app = DashboardController(); app.main_menu()
    except KeyboardInterrupt: print("\nForce Close.")