#!/usr/bin/env python3
"""
Dashboard CLI - V19 (AUTO-COOLDOWN EDITION)
Fitur:
- Auto-Cooldown (Istirahat Berkala/Micro-Sleep)
- Safety Config (Limit Harian)
- Daily Usage Tracker
- Activity Logging & Analytics
- Whitelist Manager
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
        
        if not os.path.exists("data"): os.makedirs("data")
        
        # Init Files
        self.whitelist_path = os.path.join("data", "whitelist.json")
        if not os.path.exists(self.whitelist_path):
            with open(self.whitelist_path, 'w') as f: json.dump([], f)
            
        self.log_path = os.path.join("data", "activity_log.txt")
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w') as f: f.write("=== BOT ACTIVITY LOG ===\n")

        # Config Init
        self.config_path = os.path.join("data", "config.json")
        self.usage_path = os.path.join("data", "daily_usage.json")
        self._init_safety_config()

    # =====================================================
    # ⚙️ SAFETY SYSTEM (LIMIT & COOLDOWN)
    # =====================================================
    def _init_safety_config(self):
        # Default Config
        # cooldown_threshold: Istirahat setiap 20 aksi
        # cooldown_delay: Istirahat selama 300 detik (5 menit)
        default_config = {
            "max_like": 150, "max_follow": 150, "max_unfollow": 200,
            "cooldown_threshold": 20, "cooldown_delay": 300 
        }
        if not os.path.exists(self.config_path):
            with open(self.config_path, 'w') as f: json.dump(default_config, f, indent=4)
        
        # Cek update config lama ke baru (Compatibility check)
        else:
            current_cfg = self._get_config()
            if "cooldown_threshold" not in current_cfg:
                current_cfg["cooldown_threshold"] = 20
                current_cfg["cooldown_delay"] = 300
                self._save_config(current_cfg)

        today = datetime.now().strftime("%Y-%m-%d")
        default_usage = {"date": today, "like": 0, "follow": 0, "unfollow": 0}
        if not os.path.exists(self.usage_path):
            with open(self.usage_path, 'w') as f: json.dump(default_usage, f, indent=4)

    def _get_config(self):
        with open(self.config_path, 'r') as f: return json.load(f)

    def _save_config(self, data):
        with open(self.config_path, 'w') as f: json.dump(data, f, indent=4)

    def _get_usage(self):
        with open(self.usage_path, 'r') as f: data = json.load(f)
        today = datetime.now().strftime("%Y-%m-%d")
        if data['date'] != today:
            data = {"date": today, "like": 0, "follow": 0, "unfollow": 0}
            self._save_usage(data)
        return data

    def _save_usage(self, data):
        with open(self.usage_path, 'w') as f: json.dump(data, f, indent=4)

    def _check_limit(self, action_type):
        config = self._get_config()
        usage = self._get_usage()
        limit = config.get(f"max_{action_type}", 0)
        current = usage.get(action_type, 0)
        if current >= limit:
            self.console.print(f"\n[bold red]⛔ LIMIT HARIAN TERCAPAI ({action_type.upper()})![/bold red]")
            self.console.print(f"Usage: {current}/{limit}. Istirahat dulu bos.")
            return False
        return True

    def _update_usage(self, action_type):
        usage = self._get_usage()
        usage[action_type] += 1
        self._save_usage(usage)

    def _check_cooldown(self, session_counter):
        """Logic Auto-Cooldown / Micro Sleep"""
        cfg = self._get_config()
        threshold = cfg.get("cooldown_threshold", 20)
        delay_time = cfg.get("cooldown_delay", 300)

        # Jika counter kelipatan threshold (misal 20, 40, 60...)
        if session_counter > 0 and session_counter % threshold == 0:
            self.console.print(f"\n[bold yellow]☕ WAKTUNYA ISTIRAHAT (AUTO-COOLDOWN)[/bold yellow]")
            self.console.print(f"[dim]Bot sudah bekerja {session_counter} kali. Tidur dulu {delay_time} detik...[/dim]")
            
            with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), console=self.console) as progress:
                task = progress.add_task("Cooling down...", total=delay_time)
                for _ in range(delay_time):
                    time.sleep(1)
                    progress.advance(task)
            
            self.console.print("[green]🔋 Energi pulih! Lanjut kerja...[/green]\n")

    # =====================================================
    # 🎨 HELPER UI & LOGGING
    # =====================================================
    def _clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def _format_indo(self, value):
        try: return f"[bold cyan]{int(value):,}[/bold cyan]".replace(",", ".")
        except: return str(value)

    def _log_activity(self, action, details):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {action}: {details}\n")
        except: pass

    def _banner(self):
        self._clear_screen()
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(Panel(Align.center("[bold cyan]🌐 BUCOL INSTAGRAM BOT[/bold cyan]\n[dim]v19.0 • Auto Cooldown • Anti-Ban Logic[/dim]"), style="bold blue", border_style="blue"))
        self.console.print(grid)

    def _pause(self):
        self.console.input("\n[dim]Tekan [bold white]Enter[/bold white] untuk kembali...[/dim]")

    def _loading(self, text="Memproses"):
        with self.console.status(f"[bold green]{text}...[/bold green]", spinner="dots"): time.sleep(1.0)

    # =====================================================
    # ⚙️ MENU PENGATURAN
    # =====================================================
    def settings_menu(self):
        while True:
            self._banner()
            usage = self._get_usage(); cfg = self._get_config()
            grid = Table.grid(expand=True)
            grid.add_column(); grid.add_column(justify="right")
            grid.add_row(f"[green]Like:[/green] {usage['like']}/{cfg['max_like']}", f"[green]Follow:[/green] {usage['follow']}/{cfg['max_follow']}")
            grid.add_row(f"[red]Unfollow:[/red] {usage['unfollow']}/{cfg['max_unfollow']}", f"[yellow]Cooldown:[/yellow] Tiap {cfg['cooldown_threshold']} aksi")
            
            self.console.print(Panel(grid, title="📊 Statistik & Config", style="cyan"))
            choice = questionary.select("PENGATURAN & SAFETY", choices=["✏️ Ubah Limit Harian", "💤 Ubah Setting Cooldown", "📜 Lihat Activity Log", "❌ Kembali"]).ask()
            if choice == "❌ Kembali": break
            
            if choice == "✏️ Ubah Limit Harian":
                try:
                    cfg['max_like'] = int(questionary.text(f"Max Like/hari:", default=str(cfg['max_like'])).ask())
                    cfg['max_follow'] = int(questionary.text(f"Max Follow/hari:", default=str(cfg['max_follow'])).ask())
                    cfg['max_unfollow'] = int(questionary.text(f"Max Unfollow/hari:", default=str(cfg['max_unfollow'])).ask())
                    self._save_config(cfg); self.console.print("[green]✅ Saved![/green]"); time.sleep(1)
                except: pass
            
            elif choice == "💤 Ubah Setting Cooldown":
                try:
                    self.console.print("[dim]Contoh: Istirahat setiap 20 aksi, selama 300 detik (5 menit)[/dim]")
                    cfg['cooldown_threshold'] = int(questionary.text(f"Istirahat setiap berapa aksi?", default=str(cfg['cooldown_threshold'])).ask())
                    cfg['cooldown_delay'] = int(questionary.text(f"Berapa detik tidurnya?", default=str(cfg['cooldown_delay'])).ask())
                    self._save_config(cfg); self.console.print("[green]✅ Saved![/green]"); time.sleep(1)
                except: pass

            elif choice == "📜 Lihat Activity Log": self.view_activity_log()

    def view_activity_log(self):
        self._banner()
        if not os.path.exists(self.log_path): self.console.print("[yellow]Kosong.[/yellow]")
        else:
            self.console.print(Panel("[bold cyan]📜 ACTIVITY LOG (20 Terakhir)[/bold cyan]", expand=False))
            try:
                with open(self.log_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for line in lines[-20:]:
                        line = line.strip()
                        if not line: continue
                        style = "green" if "LIKED" in line else "blue" if "FOLLOWED" in line else "red" if "UNFOLLOWED" in line else "white"
                        self.console.print(f"[{style}]{line}[/{style}]")
            except: pass
        self._pause()

    # =====================================================
    # 🤖 FITUR OTOMATISASI (DENGAN COOLDOWN)
    # =====================================================
    def feature_auto_like(self):
        if not self.client: self.console.print("[red]❌ Login dulu bos![/red]"); return
        if not self._check_limit("like"): self._pause(); return

        self.console.print(Panel("[bold cyan]❤️ AUTO LIKE ENGINE[/bold cyan]", expand=False))
        hashtag = questionary.text("Target Hashtag (tanpa #):").ask()
        if not hashtag: return
        try: limit = int(questionary.text("Jumlah Like:", default="10").ask())
        except: limit = 10
        
        sukses, gagal = 0; session_counter = 0 # Counter sesi ini
        
        with Progress(SpinnerColumn(), TextColumn("[bold blue]{task.description}"), BarColumn(), console=self.console) as progress:
            task_id = progress.add_task("Mencari Target...", total=limit)
            try:
                medias = self.client.hashtag_medias_v1(hashtag, amount=limit, tab_key="recent")
                if not medias: medias = self.client.hashtag_medias_v1(hashtag, amount=limit, tab_key="top")
                if not medias: self.console.print("[red]❌ Zonk! Kosong.[/red]"); return
                progress.update(task_id, description="Processing...", total=len(medias))
                
                for media in medias:
                    if not self._check_limit("like"): break
                    
                    # --- CEK COOLDOWN ---
                    self._check_cooldown(session_counter)

                    try:
                        time.sleep(random.uniform(3, 6))
                        self.client.media_like(media.id)
                        sukses += 1; session_counter += 1
                        
                        self._update_usage("like")
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
        if not self._check_limit("follow"): self._pause(); return

        self.console.print(Panel("[bold cyan]👥 AUTO FOLLOW (SEARCH MODE)[/bold cyan]", expand=False))
        target_username = questionary.text("Target Username (Source):").ask()
        if not target_username: return
        try: limit = int(questionary.text("Jumlah Follow:", default="10").ask())
        except: limit = 10
        sukses = 0; session_counter = 0
        
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
                    if not self._check_limit("follow"): break
                    
                    # --- CEK COOLDOWN ---
                    self._check_cooldown(session_counter)

                    user_id = uid.pk if hasattr(uid, 'pk') else uid
                    try:
                        self.client.user_follow(user_id)
                        sukses += 1; session_counter += 1
                        self._update_usage("follow")
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
        if not self._check_limit("unfollow"): self._pause(); return

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
            self.console.print(f"[bold]Kandidat:[/bold] {len(candidates)} | [green]Whitelist:[/green] {safe_count} | [red]Target:[/red] {len(targets_to_unfollow)}")
            if len(targets_to_unfollow) > limit: targets_to_unfollow = targets_to_unfollow[:limit]
            if not targets_to_unfollow: self.console.print("[green]✅ Aman![/green]"); self._pause(); return
            confirm = questionary.confirm(f"Lanjut unfollow {len(targets_to_unfollow)} akun?").ask()
            if not confirm: return
            
            sukses = 0; session_counter = 0
            with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), console=self.console) as progress:
                task = progress.add_task("Unfollowing...", total=len(targets_to_unfollow))
                for uid in targets_to_unfollow:
                    if not self._check_limit("unfollow"): break
                    
                    # --- CEK COOLDOWN ---
                    self._check_cooldown(session_counter)

                    try:
                        user_obj = following_dict.get(uid)
                        uname = user_obj.username if user_obj else str(uid)
                        self.client.user_unfollow(uid)
                        sukses += 1; session_counter += 1
                        self._update_usage("unfollow")
                        self._log_activity("UNFOLLOWED", f"@{uname}")
                        progress.console.print(f"   🗑️  Bye @{uname}")
                        progress.advance(task)
                        time.sleep(random.uniform(4, 8))
                    except Exception as e: progress.console.print(f"[red]Gagal: {e}[/red]")
            self.console.print(f"\n[green]✅ Selesai! {sukses} akun di-unfollow.[/green]")
        except Exception as e: self.console.print(f"[red]Error: {e}[/red]")
        self._pause()

    # =====================================================
    # 🔗 SISA FUNGSI (SAMA SEPERTI SEBELUMNYA)
    # =====================================================
    def whitelist_menu(self):
        while True:
            self._banner()
            current_list = self.load_whitelist()
            self.console.print(Panel(f"🛡️ WHITELIST (Daftar Kebal Unfollow)\nTotal: [bold green]{len(current_list)} akun[/bold green]", style="cyan"))
            choice = questionary.select("MENU WHITELIST", choices=["➕ Tambah Username ke Whitelist", "🗑️  Hapus Username dari Whitelist", "📋 Lihat Daftar Whitelist", "❌ Kembali"]).ask()
            if choice == "❌ Kembali": break
            if choice == "➕ Tambah Username ke Whitelist":
                u = questionary.text("Username (tanpa @):").ask()
                if u:
                    current_list = self.load_whitelist()
                    if u not in current_list: current_list.append(u); self.save_whitelist(current_list); self.console.print(f"[green]✅ @{u} sekarang AMAN![/green]")
                    else: self.console.print(f"[yellow]⚠️ @{u} sudah ada.[/yellow]")
                    time.sleep(1.5)
            elif choice == "🗑️  Hapus Username dari Whitelist":
                if not current_list: self.console.print("[red]Whitelist kosong.[/red]"); time.sleep(1); continue
                u = questionary.select("Pilih akun untuk dihapus:", choices=current_list + ["❌ Batal"]).ask()
                if u != "❌ Batal": current_list.remove(u); self.save_whitelist(current_list); self.console.print(f"[yellow]🗑️ @{u} dihapus.[/yellow]"); time.sleep(1.5)
            elif choice == "📋 Lihat Daftar Whitelist":
                if not current_list: self.console.print("[dim]Kosong.[/dim]")
                else:
                    t = Table(title="Daftar Akun Kebal")
                    t.add_column("No", style="dim"); t.add_column("Username", style="green")
                    for idx, user in enumerate(current_list, 1): t.add_row(str(idx), user)
                    self.console.print(t)
                questionary.press_any_key_to_continue().ask()

    def analytics_menu(self):
        while True:
            self._banner()
            choice = questionary.select("📊 ANALYTICS MENU", choices=["🔄 Sync Data Statistik (Auto Fetch)", "📈 Tampilkan Laporan", "❌ Kembali"]).ask()
            if choice == "❌ Kembali": break
            if choice == "🔄 Sync Data Statistik (Auto Fetch)":
                if not self.client: self.console.print("[red]❌ Login dulu bos![/red]"); self._pause(); continue
                self.console.print("[yellow]⏳ Mengambil data (Mode: Mobile API V1)...[/yellow]")
                try:
                    my_id = self.client.user_id
                    info = self.client.user_info_v1(my_id) 
                    self.console.print(Panel(f"[bold]STATUS (@{info.username})[/bold]\n\n👥 Followers : {self._format_indo(info.follower_count)}\n👤 Following : {self._format_indo(info.following_count)}\n📸 Total Post: {self._format_indo(info.media_count)}", title="Live Data", style="cyan"))
                    self.analytics.record_daily_stats(info.username, info.follower_count, info.following_count, info.media_count, 0, 0)
                    self.console.print(f"\n[green]✅ Data berhasil dicatat ke laporan harian![/green]")
                except Exception as e: self.console.print(f"[red]Gagal fetch data: {e}[/red]")
                self._pause()
            elif choice == "📈 Tampilkan Laporan":
                u = questionary.text("Username:").ask()
                if u: print("\n"); self.analytics.print_report(u); print("\n"); questionary.press_any_key_to_continue().ask()

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
            if isinstance(result, tuple) and len(result) >= 1: is_success = result[0]; self.client = result[2] if len(result) > 2 else result
            else: is_success = True if result else False; self.client = result
            if is_success: self.username = selected_user; self.console.print(f"\n[bold green]✅ Login Berhasil![/bold green] Welcome [cyan]@{selected_user}[/cyan]")
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

    def main_menu(self):
        while True:
            self._banner()
            status_text = f"● ONLINE: @{self.username}" if self.username else "○ OFFLINE"
            status_color = "green" if self.username else "red"
            self.console.print(Align.center(f"[{status_color}]{status_text}[/{status_color}]"))
            self.console.print("")
            choice = questionary.select("MENU UTAMA", choices=["🔐 Login Akun", "🤖 Fitur Bot (Like/Follow/Unfollow)", "⚙️ Pengaturan & Safety", "👤 Kelola Database Akun", "📊 Menu Analytics", "❌ Keluar"]).ask()
            if choice == "🔐 Login Akun": self.login_menu()
            elif choice == "🤖 Fitur Bot (Like/Follow/Unfollow)": self.automation_menu()
            elif choice == "⚙️ Pengaturan & Safety": self.settings_menu()
            elif choice == "👤 Kelola Database Akun": self.account_menu()
            elif choice == "📊 Menu Analytics": self.analytics_menu()
            elif choice == "❌ Keluar": self.console.print("[bold]Bye bye! 👋[/bold]"); break

    def load_whitelist(self):
        try:
            with open(self.whitelist_path, 'r') as f: return json.load(f)
        except: return []

    def save_whitelist(self, data):
        with open(self.whitelist_path, 'w') as f: json.dump(data, f, indent=4)

if __name__ == "__main__":
    try: app = DashboardController(); app.main_menu()
    except KeyboardInterrupt: print("\nForce Close.")