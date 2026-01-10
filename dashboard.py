#!/usr/bin/env python3
"""
Dashboard CLI - Final Remastered Version
Fitur:
- Login Select Mode (Anti-Typo)
- Rich UI + Indo Number Format
- Integrated with Core
"""

import os
import sys
import time
import json
from datetime import datetime

# Library UI Modern (Wajib install: pip install rich questionary)
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich import print as rprint
import questionary

# Import core modules
# Pastikan struktur folder lu bener (ada folder 'core' dan 'data')
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
        # Init Module Core
        self.account_manager = AccountManager()
        self.login_manager = LoginManager()
        self.scheduler = MultiAccountScheduler()
        self.analytics = Analytics()
        
        self.username = None
        self.client = None
        self.console = Console()

    # =====================================================
    # 🎨 HELPER UI
    # =====================================================
    def _clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def _format_indo(self, value):
        """Ubah 10000 jadi 10.000 (Bold Cyan)"""
        try:
            val_fmt = f"{int(value):,}".replace(",", ".")
            return f"[bold cyan]{val_fmt}[/bold cyan]"
        except:
            return str(value)

    def _banner(self):
        self._clear_screen()
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_row(
            Panel(
                Align.center(
                    "[bold cyan]🌐 BUCOL INSTAGRAM BOT[/bold cyan]\n"
                    "[dim]v3.0 • Smart Login • Rich UI[/dim]"
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
    # 🔑 AUTHENTICATION (SELECT MODE)
    # =====================================================
    def login_menu(self):
        self._banner()
        self.console.print(Panel("[bold green]🔐 LOGIN AREA[/bold green]", expand=False))
        
        # 1. BACA DATABASE MANUAL (Biar akurat buat list menu)
        db_path = os.path.join("data", "accounts.json")
        accounts = []
        
        if os.path.exists(db_path):
            try:
                with open(db_path, 'r') as f:
                    content = f.read().strip()
                    if content: accounts = json.loads(content)
            except: pass

        # 2. CEK KALAU KOSONG
        if not accounts:
            self.console.print("\n[bold yellow]⚠️  DATABASE AKUN KOSONG![/bold yellow]")
            self.console.print("Silakan ke menu [cyan]👤 Kelola Database Akun[/cyan] dulu.")
            self._pause()
            return

        # 3. TAMPILKAN PILIHAN
        choices = [acc['username'] for acc in accounts]
        choices.append("❌ Kembali")

        selected_user = questionary.select(
            "Pilih Akun:",
            choices=choices,
            style=questionary.Style([('qmark', 'fg:#673ab7 bold'), ('pointer', 'fg:#673ab7 bold')])
        ).ask()

        if selected_user == "❌ Kembali": return

        # 4. AMBIL PASSWORD OTOMATIS
        target_acc = next((a for a in accounts if a['username'] == selected_user), None)
        if not target_acc: return # Safety check
        password = target_acc['password']

        # 5. EKSEKUSI LOGIN
        self._loading(f"Login ke @{selected_user}")
        
        try:
            # Panggil logic core
            result = self.login_manager.login(selected_user, password)
            
            # Handle return format dari core (bisa object atau tuple)
            if isinstance(result, tuple) and len(result) >= 1:
                is_success = result[0]
                self.client = result[2] if len(result) > 2 else result
            else:
                is_success = True if result else False
                self.client = result

            if is_success:
                self.username = selected_user
                self.console.print(f"\n[bold green]✅ Login Berhasil![/bold green] Welcome [cyan]@{selected_user}[/cyan]")
                
                # Cek info device
                if hasattr(self.client, 'device_settings'):
                    dev = self.client.device_settings.get('model', 'Unknown Device')
                    self.console.print(f"[dim]📱 Connected via {dev}[/dim]")
            else:
                self.console.print(f"\n[bold red]❌ Gagal Login.[/bold red] Cek password/checkpoint.")
                
        except Exception as e:
            self.console.print(f"\n[bold red]❌ System Error:[/bold red] {e}")
            
        self._pause()

    # =====================================================
    # 👤 ACCOUNT MANAGEMENT
    # =====================================================
    def account_menu(self):
        while True:
            self._banner()
            
            choice = questionary.select(
                "👤 KELOLA AKUN",
                choices=[
                    "➕ Tambah Akun Baru",
                    "🗑️  Hapus Akun",
                    "📋 Lihat Daftar Akun",
                    "❌ Kembali"
                ]
            ).ask()

            if choice == "❌ Kembali": break

            if choice == "➕ Tambah Akun Baru":
                self.console.print("[dim]Masukkan data akun baru:[/dim]")
                u = questionary.text("Username:").ask()
                p = questionary.password("Password:").ask()
                n = questionary.text("Catatan (Opsional):").ask()
                
                if u and p:
                    self.account_manager.add_account(u, p, n)
                    self.console.print(f"[green]✅ Akun {u} berhasil disimpan![/green]")
                    time.sleep(1)
            
            elif choice == "🗑️  Hapus Akun":
                u = questionary.text("Username yg dihapus:").ask()
                if u:
                    self.account_manager.remove_account(u)
                    self.console.print("[yellow]🗑️  Akun dihapus.[/yellow]")
                    time.sleep(1)

            elif choice == "📋 Lihat Daftar Akun":
                print("\n")
                # Memanggil fungsi list dari core
                self.account_manager.list_accounts()
                print("\n")
                questionary.press_any_key_to_continue().ask()

    # =====================================================
    # 📅 SCHEDULER
    # =====================================================
    def scheduler_menu(self):
        self._banner()
        self.console.print(Panel("[cyan]📅 MULTI-ACCOUNT SCHEDULER[/cyan]", expand=False))
        self.console.print("Scheduler akan menjalankan auto task setiap interval.\n")
        
        confirm = questionary.confirm("Mulai Scheduler sekarang?").ask()
        
        if confirm:
            self._loading("Menyiapkan Scheduler")
            try:
                self.scheduler.start()
            except KeyboardInterrupt:
                self.console.print("\n[yellow]⏸️  Scheduler dihentikan.[/yellow]")
        else:
            self.console.print("[yellow]Dibatalkan.[/yellow]")
        self._pause()

    # =====================================================
    # 📊 ANALYTICS
    # =====================================================
    def analytics_menu(self):
        while True:
            self._banner()
            choice = questionary.select(
                "📊 ANALYTICS MENU",
                choices=["📝 Input Data Harian", "📈 Tampilkan Laporan", "❌ Kembali"]
            ).ask()

            if choice == "❌ Kembali": break

            if choice == "📝 Input Data Harian":
                u = questionary.text("Username:").ask()
                if not u: continue
                
                # Validasi angka biar gak error
                f = int(questionary.text("Followers:", validate=lambda x: x.isdigit()).ask())
                g = int(questionary.text("Following:", validate=lambda x: x.isdigit()).ask())
                p = int(questionary.text("Total Post:", validate=lambda x: x.isdigit()).ask())
                l = int(questionary.text("Likes (Hari ini):", validate=lambda x: x.isdigit()).ask())
                c = int(questionary.text("Comments (Hari ini):", validate=lambda x: x.isdigit()).ask())

                self.console.print(f"\n[bold]Preview:[/bold] Followers {self._format_indo(f)} | Likes {self._format_indo(l)}")
                
                self.analytics.record_daily_stats(u, f, g, p, l, c)
                self.console.print("[green]✅ Data direkam![/green]")
                self._pause()

            elif choice == "📈 Tampilkan Laporan":
                u = questionary.text("Username target:").ask()
                self.console.print(Panel(f"📊 LAPORAN: @{u}", style="cyan"))
                print("\n")
                self.analytics.print_report(u)
                print("\n")
                self._pause()

    # =====================================================
    # ⚙️ MAIN MENU
    # =====================================================
    def main_menu(self):
        while True:
            self._banner()
            
            # Status Bar Ganteng
            status_text = f"● ONLINE: @{self.username}" if self.username else "○ OFFLINE"
            status_color = "green" if self.username else "red"
            self.console.print(Align.center(f"[{status_color}]{status_text}[/{status_color}]"))
            self.console.print("")

            choice = questionary.select(
                "MENU UTAMA",
                choices=[
                    "🔐 Login Akun",
                    "👤 Kelola Database Akun",
                    "📅 Jalankan Scheduler",
                    "📊 Menu Analytics",
                    "❌ Keluar"
                ]
            ).ask()

            if choice == "🔐 Login Akun":
                self.login_menu()
            elif choice == "👤 Kelola Database Akun":
                self.account_menu()
            elif choice == "📅 Jalankan Scheduler":
                self.scheduler_menu()
            elif choice == "📊 Menu Analytics":
                self.analytics_menu()
            elif choice == "❌ Keluar":
                self.console.print("[bold]Bye bye! 👋[/bold]")
                break

if __name__ == "__main__":
    try:
        app = DashboardController()
        app.main_menu()
    except KeyboardInterrupt:
        print("\nForce Close.")