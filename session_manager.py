#!/usr/bin/env python3
"""
Session Manager - Login dan manage session Instagram
Versi gabungan dengan fitur terbaik dari kedua kode
"""

import json
import os
import glob
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    ChallengeRequired,
    TwoFactorRequired,
    LoginRequired
)
from banner import success_msg, error_msg, warning_msg, info_msg
from colorama import Fore, Style

class SessionManager:
    def __init__(self):
        self.sessions_dir = "sessions"
        self.client = Client()
        self.client.delay_range = [1, 3]  # Delay 1-3 detik antar request
        if not os.path.exists(self.sessions_dir):
            os.makedirs(self.sessions_dir)

    def get_session_file(self, username):
        """Dapatkan path file session untuk username"""
        return os.path.join(self.sessions_dir, f"{username}_session.json")

    def get_all_saved_accounts(self):
        """Ambil semua akun yang tersimpan"""
        session_files = glob.glob(os.path.join(self.sessions_dir, "*_session.json"))
        accounts = []
        for file in session_files:
            username = os.path.basename(file).replace("_session.json", "")
            accounts.append(username)
        return sorted(accounts)

    def save_session(self, username):
        """Simpan session akun ke file"""
        try:
            settings = self.client.get_settings()
            with open(self.get_session_file(username), 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            error_msg(f"Gagal menyimpan session: {str(e)}")
            return False

    def load_session(self, username):
        """Load session dari file dan test validity"""
        try:
            session_file = self.get_session_file(username)
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    settings = json.load(f)
                
                self.client.set_settings(settings)
                # Test dengan simple request untuk cek validity
                self.client.get_timeline_feed()
                return True
        except Exception as e:
            # Jika session tidak valid, hapus file
            if os.path.exists(self.get_session_file(username)):
                os.remove(self.get_session_file(username))
            return False

    def is_session_valid(self, username):
        """Cek apakah session masih valid tanpa me-load ulang"""
        try:
            session_file = self.get_session_file(username)
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    settings = json.load(f)
                
                temp_client = Client()
                temp_client.set_settings(settings)
                temp_client.get_timeline_feed()
                return True
        except Exception:
            return False

    def delete_session(self, username):
        """Hapus session akun"""
        try:
            session_file = self.get_session_file(username)
            if os.path.exists(session_file):
                os.remove(session_file)
                success_msg(f"Session @{username} berhasil dihapus!")
            else:
                warning_msg(f"Session @{username} tidak ditemukan!")
        except Exception as e:
            error_msg(f"Error saat menghapus session: {str(e)}")

    def handle_verification_challenge(self, username, password):
        """Handle Challenge Verification (Email/SMS)"""
        print(Fore.YELLOW + "\n⚠️  VERIFIKASI AKUN DIPERLUKAN!" + Style.RESET_ALL)
        try:
            check = self.client.challenge_resolve_choice()

            choices = []
            step_data = check.get('step_data', {})
            if 'phone_number' in step_data or 'phone' in step_data:
                choices.append(('SMS', '0'))
            if 'email' in step_data:
                choices.append(('Email', '1'))

            if not choices:
                warning_msg("Tidak ditemukan metode verifikasi yang dikenali.")
                return False

            print(Fore.CYAN + "\nPilih metode verifikasi yang ingin digunakan:")
            for i, (name, code) in enumerate(choices, 1):
                print(f"{i}. {name}")

            choice_input = input(Fore.YELLOW + "\nMasukkan nomor pilihan: " + Style.RESET_ALL).strip()
            try:
                choice_num = int(choice_input)
                if choice_num < 1 or choice_num > len(choices):
                    error_msg("Pilihan tidak valid!")
                    return False
            except ValueError:
                error_msg("Input harus angka!")
                return False

            method_name, method_code = choices[choice_num - 1]
            info_msg(f"Mengirim kode verifikasi lewat {method_name}...")
            self.client.challenge_code_handler(username, choice=method_code)

            code = input(Fore.YELLOW + "\nMasukkan kode verifikasi: " + Style.RESET_ALL).strip()
            if not code:
                error_msg("Kode verifikasi tidak boleh kosong!")
                return False

            if self.client.challenge_code_handler(username, code=code):
                success_msg("Verifikasi berhasil!")
                self.client.login(username, password)
                self.save_session(username)
                return True
            else:
                error_msg("Kode verifikasi salah!")
                return False

        except Exception as e:
            error_msg(f"Error saat handle verifikasi: {str(e)}")
            return False

    def handle_two_factor_auth(self, username, password):
        """Handle Two-Factor Authentication - Input kode 2FA manual"""
        print(Fore.YELLOW + "\n⚠️  AKUN MEMERLUKAN TWO-FACTOR AUTHENTICATION!" + Style.RESET_ALL)
        try:
            code = input(Fore.YELLOW + "Masukkan kode 2FA (6 digit): " + Style.RESET_ALL).strip()
            if not code or len(code) != 6:
                error_msg("Kode 2FA harus 6 digit!")
                return False

            self.client.two_factor_login = lambda: code
            self.client.login(username, password)
            self.save_session(username)
            success_msg("Login dan verifikasi 2FA berhasil!")
            return True

        except Exception as e:
            error_msg(f"Error saat verifikasi 2FA: {str(e)}")
            return False

    def login(self, username, password=None):
        """Login ke Instagram dengan session reuse"""
        # 1. Coba load session lama dulu (tanpa password)
        if self.load_session(username):
            success_msg(f"✅ Login pakai session! Selamat datang @{username}")
            return self.client

        # 2. Jika tidak ada session atau sudah invalid, minta password
        if not password:
            error_msg("Password diperlukan untuk login!")
            return None

        try:
            info_msg("🔄 Mencoba login...")
            self.client.login(username, password)
            self.save_session(username)
            success_msg(f"✅ Login berhasil! Selamat datang @{username}")
            return self.client

        except ChallengeRequired:
            warning_msg("⚠️  Akun memerlukan verifikasi challenge!")
            if self.handle_verification_challenge(username, password):
                return self.client
            return None

        except TwoFactorRequired:
            warning_msg("⚠️  Akun memerlukan Two-Factor Authentication!")
            if self.handle_two_factor_auth(username, password):
                return self.client
            return None

        except BadPassword:
            error_msg("❌ Password salah!")
            print(Fore.YELLOW + "\n💡 Tips:")
            print("  • Pastikan password benar")
            print("  • Coba reset password jika perlu")
            print("  • Atau login di browser terlebih dahulu")
            return None

        except LoginRequired:
            error_msg("❌ Diperlukan login ulang, session tidak valid.")
            return None

        except Exception as e:
            error_msg(f"❌ Error saat login: {str(e)}")
            return None
