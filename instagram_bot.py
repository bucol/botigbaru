#!/usr/bin/env python3
"""
Instagram Account Management Bot
Features:
- Session persistence (login once, use forever)
- Auto challenge/verification handler
- Check account info
- Upload profile photo
- Change name, username, bio, email
"""

import json
import os
import time
import pickle
from datetime import datetime
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword, 
    ReloginAttemptExceeded, 
    ChallengeRequired,
    SelectContactPointRecoveryForm,
    RecaptchaChallengeForm,
    FeedbackRequired,
    LoginRequired
)

class InstagramBot:
    def __init__(self):
        self.client = Client()
        self.session_file = "instagram_session.json"
        self.settings_file = "instagram_settings.json"
        self.current_user = None
        
        # Setup client dengan delay untuk avoid rate limit
        self.client.delay_range = [1, 3]
        
    def save_session(self):
        """Save session to file untuk reuse"""
        try:
            settings = self.client.get_settings()
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            print("Session berhasil disimpan!")
            return True
        except Exception as e:
            print(f"Error saat save session: {str(e)}")
            return False
    
    def load_session(self, username):
        """Load session dari file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                self.client.set_settings(settings)
                self.client.login(username, "")  # Login dengan session
                
                # Verify session masih valid
                self.client.get_timeline_feed()
                print("Session berhasil di-load!")
                return True
        except Exception as e:
            print(f"Session tidak valid atau expired: {str(e)}")
            if os.path.exists(self.settings_file):
                os.remove(self.settings_file)
            return False
    
    def handle_challenge(self, username, password):
        """Handle Instagram challenge/verification"""
        print("\n" + "="*60)
        print("AKUN KENA CHALLENGE/VERIFIKASI!")
        print("="*60)
        
        try:
            # Get challenge info
            challenge_info = self.client.challenge_code_handler
            
            print("\nInstagram meminta verifikasi akun.")
            print("Pilih metode verifikasi:")
            print("1. SMS (nomor telepon)")
            print("2. Email")
            
            choice = input("\nPilih metode (1/2): ").strip()
            
            if choice == "1":
                # SMS verification
                print("\nMengirim kode verifikasi ke nomor telepon...")
                self.client.challenge_code_handler(username, choice="0")  # 0 = phone
                
            elif choice == "2":
                # Email verification
                print("\nMengirim kode verifikasi ke email...")
                self.client.challenge_code_handler(username, choice="1")  # 1 = email
            
            else:
                print("Pilihan tidak valid!")
                return False
            
            # Input verification code
            print("\n" + "="*60)
            code = input("Masukkan kode verifikasi yang diterima: ").strip()
            
            # Submit verification code
            if self.client.challenge_code_handler(username, code=code):
                print("Verifikasi berhasil!")
                
                # Re-login setelah verifikasi
                self.client.login(username, password)
                self.save_session()
                return True
            else:
                print("Kode verifikasi salah!")
                return False
                
        except SelectContactPointRecoveryForm:
            print("\nInstagram meminta pilih metode recovery...")
            
            try:
                # Get available recovery methods
                challenge_choice = self.client.challenge_code_handler(username)
                
                print("\nPilih metode verifikasi yang tersedia:")
                print("0. SMS")
                print("1. Email")
                
                choice = input("\nPilih (0/1): ").strip()
                self.client.challenge_code_handler(username, choice=choice)
                
                code = input("\nMasukkan kode verifikasi: ").strip()
                
                if self.client.challenge_code_handler(username, code=code):
                    print("Verifikasi berhasil!")
                    self.client.login(username, password)
                    self.save_session()
                    return True
                    
            except Exception as e:
                print(f"Error: {str(e)}")
                return False
                
        except RecaptchaChallengeForm:
            print("\nInstagram meminta CAPTCHA verification...")
            print("Silakan login manual lewat aplikasi Instagram dulu")
            print("Setelah itu coba login lagi di bot ini")
            return False
            
        except Exception as e:
            print(f"Error saat handle challenge: {str(e)}")
            return False
    
    def login(self):
        """Login ke Instagram dengan auto challenge handler"""
        print("\n" + "="*60)
        print("LOGIN INSTAGRAM")
        print("="*60)
        
        username = input("Username Instagram: ").strip()
        
        # Coba load session dulu
        if self.load_session(username):
            try:
                # Get user info untuk verify
                user_info = self.client.user_info_by_username(username)
                self.current_user = user_info
                print(f"\nLogin berhasil! Selamat datang @{username}")
                return True
            except:
                pass
        
        # Kalau session gagal, login manual
        password = input("Password: ").strip()
        
        try:
            print("\nMencoba login...")
            self.client.login(username, password)
            
            # Save session setelah login berhasil
            self.save_session()
            
            # Get user info
            user_info = self.client.user_info_by_username(username)
            self.current_user = user_info
            
            print(f"\nLogin berhasil! Selamat datang @{username}")
            return True
            
        except ChallengeRequired as e:
            print("\nAkun memerlukan verifikasi!")
            return self.handle_challenge(username, password)
            
        except BadPassword:
            print("\nPassword salah!")
            return False
            
        except ReloginAttemptExceeded:
            print("\nTerlalu banyak percobaan login!")
            print("Tunggu beberapa menit dan coba lagi")
            return False
            
        except FeedbackRequired as e:
            print("\nAkun terkena pembatasan Instagram!")
            print(f"Pesan: {str(e)}")
            print("Silakan login lewat aplikasi Instagram dulu")
            return False
            
        except Exception as e:
            print(f"\nError saat login: {str(e)}")
            print("\nKemungkinan penyebab:")
            print("   1. Username atau password salah")
            print("   2. Akun kena checkpoint/verifikasi")
            print("   3. IP kena rate limit")
            print("   4. Perlu verifikasi 2FA")
            return False
    
    def show_account_info(self):
        """Tampilkan info akun Instagram"""
        if not self.current_user:
            print("\nAnda harus login terlebih dahulu!")
            return
        
        try:
            # Refresh user info
            user_info = self.client.user_info(self.current_user.pk)
            
            print("\n" + "="*60)
            print("INFORMASI AKUN INSTAGRAM")
            print("="*60)
            print(f"User ID         : {user_info.pk}")
            print(f"Username        : @{user_info.username}")
            print(f"Full Name       : {user_info.full_name}")
            print(f"Biography       : {user_info.biography or '(kosong)'}")
            print(f"Email           : {user_info.public_email or '(tidak public)'}")
            print(f"Followers       : {user_info.follower_count:,}")
            print(f"Following       : {user_info.following_count:,}")
            print(f"Posts           : {user_info.media_count:,}")
            print(f"Is Private      : {'Ya' if user_info.is_private else 'Tidak'}")
            print(f"Is Verified     : {'Ya' if user_info.is_verified else 'Tidak'}")
            print(f"Profile Picture : {user_info.profile_pic_url}")
            print(f"External URL    : {user_info.external_url or '(tidak ada)'}")
            print("="*60)
            
        except Exception as e:
            print(f"\nError saat mengambil info akun: {str(e)}")
    
    def upload_profile_picture(self):
        """Upload foto profil Instagram"""
        if not self.current_user:
            print("\nAnda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*60)
        print("UPLOAD FOTO PROFIL")
        print("="*60)
        
        file_path = input("Masukkan path file foto: ").strip()
        
        if not os.path.exists(file_path):
            print("File tidak ditemukan!")
            return
        
        try:
            print("\nMengupload foto profil...")
            self.client.account_change_picture(file_path)
            print("Foto profil berhasil diupload!")
            
        except Exception as e:
            print(f"Error saat upload foto: {str(e)}")
    
    def change_name(self):
        """Ganti nama lengkap Instagram"""
        if not self.current_user:
            print("\nAnda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*60)
        print("GANTI NAMA LENGKAP")
        print("="*60)
        
        user_info = self.client.user_info(self.current_user.pk)
        print(f"Nama sekarang: {user_info.full_name}")
        
        new_name = input("\nNama baru: ").strip()
        
        if not new_name:
            print("Nama tidak boleh kosong!")
            return
        
        try:
            print("\nMengubah nama...")
            self.client.account_edit(full_name=new_name)
            print(f"Nama berhasil diubah menjadi: {new_name}")
            
        except Exception as e:
            print(f"Error saat ganti nama: {str(e)}")
    
    def change_username(self):
        """Ganti username Instagram"""
        if not self.current_user:
            print("\nAnda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*60)
        print("GANTI USERNAME")
        print("="*60)
        print("WARNING: Ganti username adalah perubahan PERMANEN!")
        print("Username lama akan tersedia untuk diambil orang lain!")
        
        user_info = self.client.user_info(self.current_user.pk)
        print(f"\nUsername sekarang: @{user_info.username}")
        
        new_username = input("\nUsername baru: ").strip()
        
        if not new_username:
            print("Username tidak boleh kosong!")
            return
        
        confirm = input(f"\nYakin ingin ganti username ke @{new_username}? (yes/no): ").strip().lower()
        
        if confirm != "yes":
            print("Dibatalkan!")
            return
        
        try:
            print("\nMengubah username...")
            self.client.account_edit(username=new_username)
            print(f"Username berhasil diubah menjadi: @{new_username}")
            
            # Update session dengan username baru
            self.save_session()
            
        except Exception as e:
            print(f"Error saat ganti username: {str(e)}")
            print("Kemungkinan username sudah dipakai atau tidak valid")
    
    def change_bio(self):
        """Ganti bio Instagram"""
        if not self.current_user:
            print("\nAnda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*60)
        print("GANTI BIO")
        print("="*60)
        
        user_info = self.client.user_info(self.current_user.pk)
        print(f"Bio sekarang: {user_info.biography or '(kosong)'}")
        
        print("\nMasukkan bio baru (tekan Enter 2x untuk selesai):")
        lines = []
        while True:
            line = input()
            if line == "" and len(lines) > 0:
                break
            lines.append(line)
        
        new_bio = "\n".join(lines)
        
        try:
            print("\nMengubah bio...")
            self.client.account_edit(biography=new_bio)
            print("Bio berhasil diubah!")
            
        except Exception as e:
            print(f"Error saat ganti bio: {str(e)}")
    
    def change_email(self):
        """Ganti email Instagram"""
        if not self.current_user:
            print("\nAnda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*60)
        print("GANTI EMAIL")
        print("="*60)
        print("WARNING: Fitur ganti email memerlukan verifikasi dari Instagram!")
        
        user_info = self.client.user_info(self.current_user.pk)
        print(f"\nEmail sekarang: {user_info.public_email or '(tidak tersedia)'}")
        
        new_email = input("\nEmail baru: ").strip()
        
        if not new_email:
            print("Email tidak boleh kosong!")
            return
        
        try:
            print("\nMengubah email...")
            self.client.account_edit(email=new_email)
            print("Email berhasil diubah!")
            print("Cek email baru untuk verifikasi dari Instagram")
            
        except Exception as e:
            print(f"Error saat ganti email: {str(e)}")
    
    def logout(self):
        """Logout dan hapus session"""
        try:
            self.client.logout()
            if os.path.exists(self.settings_file):
                os.remove(self.settings_file)
            self.current_user = None
            print("\nLogout berhasil! Session telah dihapus.")
        except Exception as e:
            print(f"\nError saat logout: {str(e)}")
    
    def show_main_menu(self):
        """Tampilkan menu utama"""
        while True:
            print("\n" + "="*60)
            print("MENU UTAMA - INSTAGRAM BOT")
            print("="*60)
            print("1. Lihat Info Akun")
            print("2. Upload Foto Profil")
            print("3. Ganti Nama Lengkap")
            print("4. Ganti Username")
            print("5. Ganti Bio")
            print("6. Ganti Email")
            print("7. Logout")
            print("="*60)
            
            choice = input("Pilih menu (1-7): ").strip()
            
            if choice == '1':
                self.show_account_info()
            elif choice == '2':
                self.upload_profile_picture()
            elif choice == '3':
                self.change_name()
            elif choice == '4':
                self.change_username()
            elif choice == '5':
                self.change_bio()
            elif choice == '6':
                self.change_email()
            elif choice == '7':
                self.logout()
                break
            else:
                print("Pilihan tidak valid!")

if __name__ == "__main__":
    bot = InstagramBot()
    if bot.login():
        bot.show_main_menu()