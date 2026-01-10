#!/usr/bin/env python3
"""
Dashboard CLI - V10 (COMPLETE RESTORED)
Fitur:
- Login Select Mode
- Database Management
- Auto Like & Auto Follow (RESTORED)
- Rich UI + Indo Format
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
        self.client = None # Object Client Instagram disimpan disini
        self.console = Console()

    # =====================================================
    # 🎨 HELPER UI
    # =====================================================
    def _clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def _format_indo(self, value):
        try:
            val_fmt = f"{int(value):,}".replace(",", ".")
            return f"[bold cyan]{val_fmt}[/bold cyan]"
        except: return str(value)

    def _banner(self):
        self._clear_screen()
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(
            Panel(
                Align.center(
                    "[bold cyan]🌐 BUCOL INSTAGRAM BOT[/bold cyan]\n"
                    "[dim]v10.0 • Features Restored • Auto Like Ready[/dim]"
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
    # 🤖 FITUR OTOMATISASI (AUTO LIKE & FOLLOW) - INI YANG TADI ILANG
    # =====================================================
    def feature_auto_like(self):
        if not self.client:
            self.console.print("[red]❌ Eits, Login dulu bos![/red]")
            return

        self.console.print(Panel("[bold cyan]❤️ AUTO LIKE ENGINE[/bold cyan]", expand=False))
        hashtag = questionary.text("Target Hashtag (tanpa #):").ask()
        if not hashtag: return
        
        try:
            limit = int(questionary.text("Jumlah Like:", default="10").ask())
        except: limit = 10
        
        sukses, gagal = 0, 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=None, style="dim", complete_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console
        ) as progress:
            
            task_id = progress.add_task("Mencari Target...", total=limit)
            
            try:
                # Menggunakan client yang sudah login
                medias = self.client.hashtag_medias_v1(hashtag, amount=limit, tab_key="recent")
                
                if not medias:
                    progress.update(task_id, description="[yellow]Switch ke Top Posts...[/yellow]")
                    medias = self.client.hashtag_medias_v1(hashtag, amount=limit, tab_key="top")
                
                if not medias:
                    self.console.print("[red]❌ Zonk! Tidak ada postingan ditemukan.[/red]")
                    return

                progress.update(task_id, description="Processing...", total=len(medias))
                
                for media in medias:
                    try:
                        # Simulasi Delay Manusia
                        time.sleep(random.uniform(2, 5))
                        
                        self.client.media_like(media.id)
                        sukses += 1
                        progress.console.print(f"   ✅ Liked: [dim]{media.code}[/dim]")
                        progress.advance(task_id)
                        
                        # Delay antar like
                        time.sleep(random.uniform(3, 8))
                        
                    except Exception as e:
                        gagal += 1
                        if "feedback_required" in str(e).lower():
                            progress.console.print("[bold red]⚠️ SOFTBAN DETECTED! Berhenti...[/bold red]")
                            break
                            
            except Exception as e:
                self.console.print(f"[red]Error System: {e}[/red]")
                
        self.console.print(f"\n[green]✅ Selesai! Sukses: {sukses} | Gagal: {gagal}[/green]")
        self._pause()

    def feature_auto_follow(self):
        if not self.client:
            self.console.print("[red]❌ Login dulu bos![/red]")
            return

        self.console.print(Panel("[bold cyan]👥 AUTO FOLLOW ENGINE[/bold cyan]", expand=False))
        target = questionary.text("Target Username (Ambil follower dia):").ask()
        if not target: return
        
        try:
            limit = int(questionary.text("Jumlah Follow:", default="10").ask())
        except: limit = 10
        
        sukses = 0
        
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), console=self.console) as progress:
            task = progress.add_task("Scraping...", total=limit)
            try:
                target_id = self.client.user_id_from_username(target)
                followers = self.client.user_followers(target_id, amount=limit)
                
                progress.update(task, description="Following...", total=len(followers))
                
                for uid in followers:
                    try:
                        self.client.user_follow(uid)
                        sukses += 1
                        progress.console.print(f"   ➕ Followed: {uid}")
                        progress.advance(task)
                        time.sleep(random.uniform(4, 10))
                    except: pass
            except Exception as e:
                self.console.print(f"[red]Error: {e}[/red]")
                
        self.console.print(f"\n[green]✅ Selesai! Sukses: {sukses}[/green]")
        self._pause()

    def automation_menu(self):
        while True:
            self._banner()
            if not self.client:
                self.console.print("[bold red]⚠️ PERINGATAN:[/bold red] Kamu BELUM LOGIN.")
                self.console.print("Fitur ini tidak akan jalan. Silakan Login dulu di Menu Utama.\n")
            
            choice = questionary.select(
                "🤖 FITUR OTOMATISASI",
                choices=[
                    "❤️ Auto Like (Hashtag)",
                    "👥 Auto Follow (Target User)",
                    "❌ Kembali"
                ]
            ).ask()

            if choice == "❌ Kembali": break
            
            if choice == "❤️ Auto Like (Hashtag)":
                self.feature_auto_like()
            elif choice == "👥 Auto Follow (Target User)":
                self.feature_auto_follow()

    # =====================================================
    # 🔑 AUTHENTICATION & ACCOUNT
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

        if not accounts:
            self.console.print("\n[bold yellow]⚠️  DATABASE KOSONG![/bold yellow]")
            self.console.print("Ke menu [cyan]👤 Kelola Database Akun[/cyan] dulu ya.")
            self._pause()
            return

        choices = [acc['username'] for acc in accounts] + ["❌ Kembali"]
        selected_user = questionary.select("Pilih Akun:", choices=choices).ask()

        if selected_user == "❌ Kembali": return

        target_acc = next((a for a in accounts if a['username'] == selected_user), None)
        password = target_acc['password']

        self._loading(f"Login ke @{selected_user}")
        try:
            result = self.login_manager.login(selected_user, password)
            
            # Flexible handling
            if isinstance(result, tuple) and len(result) >= 1:
                is_success = result[0]
                self.client = result[2] if len(result) > 2 else result
            else:
                is_success = True if result else False
                self.client = result

            if is_success:
                self.username = selected_user
                self.console.print(f"\n[bold green]✅ Login Berhasil![/bold green] Welcome [cyan]@{selected_user}[/cyan]")
                if hasattr(self.client, 'device_settings'):
                    dev = self.client.device_settings.get('model', 'Unknown')
                    self.console.print(f"[dim]📱 Device: {dev}[/dim]")
            else:
                self.console.print(f"\n[bold red]❌ Gagal Login.[/bold red] Cek password.")
        except Exception as e:
            self.console.print(f"\n[bold red]❌ Error: {e}[/bold red]")
        self._pause()

    def account_menu(self):
        while True:
            self._banner()
            choice = questionary.select(
                "👤 KELOLA AKUN",
                choices=["➕ Tambah Akun Baru", "🗑️  Hapus Akun", "📋 Lihat Daftar Akun", "❌ Kembali"]
            ).ask()

            if choice == "❌ Kembali": break
            if choice == "➕ Tambah Akun Baru":
                u = questionary.text("Username:").ask()
                p = questionary.password("Password:").ask()
                if u and p:
                    self.account_manager.add_account(u, p)
                    self.console.print(f"[green]✅ Akun {u} disimpan![/green]")
                    time.sleep(1)
            elif choice == "🗑️  Hapus Akun":
                u = questionary.text("Username dihapus:").ask()
                if u:
                    self.account_manager.remove_account(u)
                    self.console.print("[yellow]🗑️  Dihapus.[/yellow]")
                    time.sleep(1)
            elif choice == "📋 Lihat Daftar Akun":
                print("\n"); self.account_manager.list_accounts(); print("\n")
                questionary.press_any_key_to_continue().ask()

    # =====================================================
    # ⚙️ MAIN MENU
    # =====================================================
    def main_menu(self):
        while True:
            self._banner()
            
            status_text = f"● ONLINE: @{self.username}" if self.username else "○ OFFLINE"
            status_color = "green" if self.username else "red"
            self.console.print(Align.center(f"[{status_color}]{status_text}[/{status_color}]"))
            self.console.print("")

            # MENU LENGKAP IS BACK!
            choice = questionary.select(
                "MENU UTAMA",
                choices=[
                    "🔐 Login Akun",
                    "🤖 Fitur Bot (Auto Like/Follow)",  # <--- INI DIA YANG DITUNGGU
                    "👤 Kelola Database Akun",
                    "📊 Menu Analytics",
                    "❌ Keluar"
                ]
            ).ask()

            if choice == "🔐 Login Akun":
                self.login_menu()
            elif choice == "🤖 Fitur Bot (Auto Like/Follow)":
                self.automation_menu()
            elif choice == "👤 Kelola Database Akun":
                self.account_menu()
            elif choice == "📊 Menu Analytics":
                # Analytics menu code simplified for brevity
                u = questionary.text("Cek Laporan Username:").ask()
                if u: 
                    print("\n"); self.analytics.print_report(u); print("\n")
                    questionary.press_any_key_to_continue().ask()
            elif choice == "❌ Keluar":
                self.console.print("[bold]Bye bye! 👋[/bold]")
                break

if __name__ == "__main__":
    try:
        app = DashboardController()
        app.main_menu()
    except KeyboardInterrupt:
        print("\nForce Close.")