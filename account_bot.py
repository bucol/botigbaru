#!/usr/bin/env python3
"""
User Account Management Bot
Compatible with Termux and PC
Features: Check account info, upload profile photo, change name, username, bio, and email
"""

import sqlite3
import json
import os
import re
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

class AccountBot:
    def __init__(self):
        self.db_name = "accounts.db"
        self.profile_pics_dir = "profile_pictures"
        self.current_user = None
        self.setup_database()
        self.setup_directories()
    
    def setup_directories(self):
        """Create necessary directories for storing profile pictures"""
        if not os.path.exists(self.profile_pics_dir):
            os.makedirs(self.profile_pics_dir)
    
    def setup_database(self):
        """Initialize SQLite database with users table"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                bio TEXT,
                profile_picture TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password):
        """Hash password using SHA-256 (hashlib)"""
        return hashlib.sha256(password.encode('utf-8')).hexdigest()
    
    def verify_password(self, password, hashed):
        """Verify password against hashed password"""
        return self.hash_password(password) == hashed
    
    def validate_email(self, email):
        """Validate email format using regex"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def validate_username(self, username):
        """Validate username (alphanumeric and underscore, 3-20 chars)"""
        pattern = r'^[a-zA-Z0-9_]{3,20}$'
        return re.match(pattern, username) is not None
    
    def register_user(self):
        """Register a new user"""
        print("\n" + "="*50)
        print("REGISTRASI USER BARU")
        print("="*50)
        
        # Get username
        while True:
            username = input("Username (3-20 karakter, huruf, angka, underscore): ").strip()
            if not self.validate_username(username):
                print("❌ Username tidak valid! Harus 3-20 karakter (huruf, angka, underscore)")
                continue
            
            # Check if username exists
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                print("❌ Username sudah digunakan!")
                continue
            conn.close()
            break
        
        # Get name
        name = input("Nama lengkap: ").strip()
        while not name:
            print("❌ Nama tidak boleh kosong!")
            name = input("Nama lengkap: ").strip()
        
        # Get email
        while True:
            email = input("Email: ").strip()
            if not self.validate_email(email):
                print("❌ Format email tidak valid!")
                continue
            
            # Check if email exists
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            if cursor.fetchone():
                conn.close()
                print("❌ Email sudah digunakan!")
                continue
            conn.close()
            break
        
        # Get password
        while True:
            password = input("Password (min 6 karakter): ").strip()
            if len(password) < 6:
                print("❌ Password minimal 6 karakter!")
                continue
            
            confirm_password = input("Konfirmasi password: ").strip()
            if password != confirm_password:
                print("❌ Password tidak cocok!")
                continue
            break
        
        # Get bio (optional)
        bio = input("Bio (opsional, tekan Enter untuk skip): ").strip()
        
        # Hash password
        hashed_password = self.hash_password(password)
        
        # Insert into database
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO users (username, name, email, password, bio, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, name, email, hashed_password, bio, now, now))
        
        conn.commit()
        conn.close()
        
        print("\n✅ Registrasi berhasil! Silakan login.")
    
    def login(self):
        """Login user"""
        print("\n" + "="*50)
        print("LOGIN")
        print("="*50)
        
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and self.verify_password(password, user[4]):  # user[4] is password
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'name': user[2],
                'email': user[3],
                'password': user[4],
                'bio': user[5],
                'profile_picture': user[6],
                'created_at': user[7],
                'updated_at': user[8]
            }
            print(f"\n✅ Login berhasil! Selamat datang, {self.current_user['name']}!")
            return True
        else:
            print("\n❌ Username atau password salah!")
            return False
    
    def show_account_info(self):
        """Display current user's account information"""
        if not self.current_user:
            print("\n❌ Anda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*50)
        print("INFORMASI AKUN")
        print("="*50)
        print(f"ID              : {self.current_user['id']}")
        print(f"Username        : {self.current_user['username']}")
        print(f"Nama            : {self.current_user['name']}")
        print(f"Email           : {self.current_user['email']}")
        print(f"Bio             : {self.current_user['bio'] or '(belum diisi)'}")
        print(f"Foto Profil     : {self.current_user['profile_picture'] or '(belum diupload)'}")
        print(f"Dibuat          : {self.current_user['created_at']}")
        print(f"Terakhir Update : {self.current_user['updated_at']}")
        print("="*50)
    
    def upload_profile_picture(self):
        """Upload profile picture"""
        if not self.current_user:
            print("\n❌ Anda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*50)
        print("UPLOAD FOTO PROFIL")
        print("="*50)
        
        file_path = input("Masukkan path file gambar: ").strip()
        
        # Check if file exists
        if not os.path.exists(file_path):
            print("❌ File tidak ditemukan!")
            return
        
        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in valid_extensions:
            print(f"❌ Format file tidak didukung! Gunakan: {', '.join(valid_extensions)}")
            return
        
        # Create new filename
        new_filename = f"user_{self.current_user['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}{file_ext}"
        new_path = os.path.join(self.profile_pics_dir, new_filename)
        
        # Copy file
        try:
            shutil.copy2(file_path, new_path)
            
            # Update database
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            now = datetime.now().isoformat()
            
            cursor.execute('''
                UPDATE users 
                SET profile_picture = ?, updated_at = ?
                WHERE id = ?
            ''', (new_path, now, self.current_user['id']))
            
            conn.commit()
            conn.close()
            
            # Update current user
            self.current_user['profile_picture'] = new_path
            self.current_user['updated_at'] = now
            
            print(f"\n✅ Foto profil berhasil diupload: {new_path}")
        except Exception as e:
            print(f"❌ Error saat upload: {str(e)}")
    
    def change_name(self):
        """Change user's name"""
        if not self.current_user:
            print("\n❌ Anda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*50)
        print("GANTI NAMA")
        print("="*50)
        print(f"Nama sekarang: {self.current_user['name']}")
        
        new_name = input("Nama baru: ").strip()
        while not new_name:
            print("❌ Nama tidak boleh kosong!")
            new_name = input("Nama baru: ").strip()
        
        # Update database
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE users 
            SET name = ?, updated_at = ?
            WHERE id = ?
        ''', (new_name, now, self.current_user['id']))
        
        conn.commit()
        conn.close()
        
        # Update current user
        self.current_user['name'] = new_name
        self.current_user['updated_at'] = now
        
        print(f"\n✅ Nama berhasil diubah menjadi: {new_name}")
    
    def change_username(self):
        """Change username"""
        if not self.current_user:
            print("\n❌ Anda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*50)
        print("GANTI USERNAME")
        print("="*50)
        print(f"Username sekarang: {self.current_user['username']}")
        
        while True:
            new_username = input("Username baru (3-20 karakter): ").strip()
            if not self.validate_username(new_username):
                print("❌ Username tidak valid! Harus 3-20 karakter (huruf, angka, underscore)")
                continue
            
            # Check if username exists
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ? AND id != ?", 
                          (new_username, self.current_user['id']))
            if cursor.fetchone():
                conn.close()
                print("❌ Username sudah digunakan!")
                continue
            
            # Update database
            now = datetime.now().isoformat()
            cursor.execute('''
                UPDATE users 
                SET username = ?, updated_at = ?
                WHERE id = ?
            ''', (new_username, now, self.current_user['id']))
            
            conn.commit()
            conn.close()
            
            # Update current user
            self.current_user['username'] = new_username
            self.current_user['updated_at'] = now
            
            print(f"\n✅ Username berhasil diubah menjadi: {new_username}")
            break
    
    def change_bio(self):
        """Change user's bio"""
        if not self.current_user:
            print("\n❌ Anda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*50)
        print("GANTI BIO")
        print("="*50)
        print(f"Bio sekarang: {self.current_user['bio'] or '(belum diisi)'}")
        
        new_bio = input("Bio baru: ").strip()
        
        # Update database
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        now = datetime.now().isoformat()
        
        cursor.execute('''
            UPDATE users 
            SET bio = ?, updated_at = ?
            WHERE id = ?
        ''', (new_bio, now, self.current_user['id']))
        
        conn.commit()
        conn.close()
        
        # Update current user
        self.current_user['bio'] = new_bio
        self.current_user['updated_at'] = now
        
        print(f"\n✅ Bio berhasil diubah!")
    
    def change_email(self):
        """Change user's email"""
        if not self.current_user:
            print("\n❌ Anda harus login terlebih dahulu!")
            return
        
        print("\n" + "="*50)
        print("GANTI EMAIL")
        print("="*50)
        print(f"Email sekarang: {self.current_user['email']}")
        
        while True:
            new_email = input("Email baru: ").strip()
            if not self.validate_email(new_email):
                print("❌ Format email tidak valid!")
                continue
            
            # Check if email exists
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE email = ? AND id != ?", 
                          (new_email, self.current_user['id']))
            if cursor.fetchone():
                conn.close()
                print("❌ Email sudah digunakan!")
                continue
            
            # Verify current password for security
            password = input("Masukkan password untuk konfirmasi: ").strip()
            if not self.verify_password(password, self.current_user['password']):
                conn.close()
                print("❌ Password salah!")
                return
            
            # Update database
            now = datetime.now().isoformat()
            cursor.execute('''
                UPDATE users 
                SET email = ?, updated_at = ?
                WHERE id = ?
            ''', (new_email, now, self.current_user['id']))
            
            conn.commit()
            conn.close()
            
            # Update current user
            self.current_user['email'] = new_email
            self.current_user['updated_at'] = now
            
            print(f"\n✅ Email berhasil diubah menjadi: {new_email}")
            break
    
    def show_main_menu(self):
        """Display main menu for logged-in users"""
        while True:
            print("\n" + "="*50)
            print("MENU UTAMA")
            print("="*50)
            print("1. Lihat Info Akun")
            print("2. Upload Foto Profil")
            print("3. Ganti Nama")
            print("4. Ganti Username")
            print("5. Ganti Bio")
            print("6. Ganti Email")
            print("7. Logout")
            print("0. Keluar")
            print("="*50)
            
            choice = input("Pilih menu (0-7): ").strip()
            
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
                print("\n✅ Logout berhasil!")
                self.current_user = None
                break
            elif choice == '0':
                print("\nTerima kasih! Sampai jumpa!")
                return False
            else:
                print("\n❌ Pilihan tidak valid!")
        
        return True
    
    def run(self):
        """Main application loop"""
        print("="*50)
        print("BOT MANAJEMEN AKUN USER")
        print("="*50)
        print("Selamat datang di Bot Manajemen Akun!")
        
        while True:
            if not self.current_user:
                print("\n" + "="*50)
                print("MENU LOGIN")
                print("="*50)
                print("1. Login")
                print("2. Registrasi")
                print("0. Keluar")
                print("="*50)
                
                choice = input("Pilih menu (0-2): ").strip()
                
                if choice == '1':
                    if self.login():
                        if not self.show_main_menu():
                            break
                elif choice == '2':
                    self.register_user()
                elif choice == '0':
                    print("\nTerima kasih! Sampai jumpa!")
                    break
                else:
                    print("\n❌ Pilihan tidak valid!")
            else:
                if not self.show_main_menu():
                    break

def main():
    """Main entry point"""
    try:
        bot = AccountBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n\nProgram dihentikan oleh user. Terima kasih!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
