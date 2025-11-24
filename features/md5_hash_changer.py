#!/usr/bin/env python3
"""
MD5 Hash Changer
Ubah MD5 hash file foto untuk menghindari deteksi Instagram
Dengan opsi random dan batch processing
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import os
import hashlib
from PIL import Image
import random

class MD5HashChanger:
    def __init__(self):
        self.profile_pic_folder = "profile_pictures"
        self.posts_photos_folder = "posts_photos"
        self.posts_reels_folder = "posts_reels"

    def get_file_md5(self, file_path):
        """Hitung MD5 hash file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            error_msg(f"Error hitung MD5: {str(e)}")
            return None

    def change_image_md5(self, file_path):
        """Ubah MD5 file gambar dengan modifikasi minor (compression, metadata)"""
        try:
            # Baca gambar
            img = Image.open(file_path)
            
            # Ubah quality/compression dengan variasi random untuk hasil yang berbeda setiap kali
            quality_variation = random.randint(90, 98)
            temp_path = file_path + ".tmp"
            
            if img.format == 'JPEG':
                img.save(temp_path, 'JPEG', quality=quality_variation, optimize=True)
            elif img.format == 'PNG':
                img.save(temp_path, 'PNG', optimize=True)
            else:
                img.save(temp_path)
            
            # Replace file asli
            os.remove(file_path)
            os.rename(temp_path, file_path)
            
            return True
        except Exception as e:
            error_msg(f"Error ubah MD5: {str(e)}")
            if os.path.exists(file_path + ".tmp"):
                os.remove(file_path + ".tmp")
            return False

    def change_md5_for_files(self, folder):
        """Ubah MD5 untuk semua file di folder tertentu"""
        try:
            if not os.path.exists(folder):
                warning_msg(f"Folder '{folder}' tidak ditemukan!")
                return False

            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
            image_files = [f for f in os.listdir(folder) 
                          if os.path.isfile(os.path.join(folder, f)) 
                          and f.lower().endswith(image_extensions)]

            if not image_files:
                warning_msg(f"Tidak ada file gambar di folder '{folder}'")
                return False

            info_msg(f"Mengubah MD5 untuk {len(image_files)} file...")
            changed_count = 0
            
            for i, filename in enumerate(image_files, 1):
                file_path = os.path.join(folder, filename)
                
                old_md5 = self.get_file_md5(file_path)
                print(Fore.YELLOW + f"\n{i}. {filename}" + Style.RESET_ALL)
                print(f"   MD5 lama: {old_md5}")
                
                if self.change_image_md5(file_path):
                    new_md5 = self.get_file_md5(file_path)
                    print(Fore.GREEN + f"   MD5 baru: {new_md5}" + Style.RESET_ALL)
                    print(Fore.GREEN + "   ✅ Ubah MD5 berhasil" + Style.RESET_ALL)
                    changed_count += 1
                else:
                    print(Fore.RED + "   ❌ Gagal ubah MD5" + Style.RESET_ALL)

            success_msg(f"\n✅ {changed_count}/{len(image_files)} file berhasil diubah MD5-nya!")
            return True

        except Exception as e:
            error_msg(f"Error change MD5 for files: {str(e)}")
            return False

    def change_random_file_md5(self, folder):
        """Ubah MD5 file random dari folder (untuk 1 file saja)"""
        try:
            if not os.path.exists(folder):
                warning_msg(f"Folder '{folder}' tidak ditemukan!")
                return False

            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
            image_files = [f for f in os.listdir(folder) 
                          if os.path.isfile(os.path.join(folder, f)) 
                          and f.lower().endswith(image_extensions)]

            if not image_files:
                warning_msg(f"Tidak ada file gambar di folder '{folder}'")
                return False

            # Ambil 1 file random
            random_file = random.choice(image_files)
            file_path = os.path.join(folder, random_file)
            
            print(Fore.YELLOW + f"\n📁 File random yang dipilih: {random_file}" + Style.RESET_ALL)
            
            old_md5 = self.get_file_md5(file_path)
            print(f"   MD5 lama: {old_md5}")
            
            if self.change_image_md5(file_path):
                new_md5 = self.get_file_md5(file_path)
                print(Fore.GREEN + f"   MD5 baru: {new_md5}" + Style.RESET_ALL)
                print(Fore.GREEN + "   ✅ Ubah MD5 berhasil" + Style.RESET_ALL)
                return True
            else:
                print(Fore.RED + "   ❌ Gagal ubah MD5" + Style.RESET_ALL)
                return False

        except Exception as e:
            error_msg(f"Error change random file MD5: {str(e)}")
            return False

    def auto_change_md5_before_upload(self, file_path):
        """Ubah MD5 file sebelum digunakan (untuk posting)"""
        try:
            return self.change_image_md5(file_path)
        except Exception as e:
            error_msg(f"Error auto change MD5: {str(e)}")
            return False

    def md5_changer_menu(self):
        """Menu ubah MD5 file"""
        while True:
            show_separator()
            print(Fore.CYAN + "\n🔐 MD5 HASH CHANGER" + Style.RESET_ALL)
            show_separator()
            print(Fore.YELLOW + "\n1. 🔄 Ubah MD5 - Foto Profile (Semua)")
            print("2. 🔄 Ubah MD5 - Foto Postingan (Semua)")
            print("3. 🎲 Ubah MD5 - Random File (Foto Profile)")
            print("4. 🎲 Ubah MD5 - Random File (Foto Postingan)")
            print("5. 📋 Cek MD5 Hash Semua File")
            print("6. 🔄 Ubah MD5 Semua Folder (Batch)")
            print("0. ❌ Kembali" + Style.RESET_ALL)
            show_separator()

            choice = input(Fore.MAGENTA + "\nPilih menu (0-6): " + Style.RESET_ALL).strip()

            if choice == '1':
                self.change_md5_for_files(self.profile_pic_folder)
            elif choice == '2':
                self.change_md5_for_files(self.posts_photos_folder)
            elif choice == '3':
                self.change_random_file_md5(self.profile_pic_folder)
            elif choice == '4':
                self.change_random_file_md5(self.posts_photos_folder)
            elif choice == '5':
                self.check_all_md5()
            elif choice == '6':
                print(Fore.YELLOW + "\nUbah MD5 untuk semua folder..." + Style.RESET_ALL)
                self.change_md5_for_files(self.profile_pic_folder)
                print()
                self.change_md5_for_files(self.posts_photos_folder)
            elif choice == '0':
                info_msg("Kembali ke menu utama...")
                break
            else:
                error_msg("Pilihan tidak valid!")

            input(Fore.CYAN + "\nTekan Enter untuk lanjut..." + Style.RESET_ALL)

    def check_all_md5(self):
        """Cek MD5 semua file di semua folder"""
        show_separator()
        print(Fore.CYAN + "\n📋 DAFTAR MD5 HASH SEMUA FILE" + Style.RESET_ALL)
        show_separator()

        folders = {
            'Foto Profile': self.profile_pic_folder,
            'Foto Postingan': self.posts_photos_folder,
        }

        for folder_name, folder_path in folders.items():
            if not os.path.exists(folder_path):
                continue

            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
            image_files = [f for f in os.listdir(folder_path) 
                          if os.path.isfile(os.path.join(folder_path, f)) 
                          and f.lower().endswith(image_extensions)]

            if image_files:
                print(Fore.YELLOW + f"\n📁 {folder_name}:" + Style.RESET_ALL)
                for filename in sorted(image_files):
                    file_path = os.path.join(folder_path, filename)
                    md5 = self.get_file_md5(file_path)
                    print(f"  {filename}")
                    print(f"  MD5: {md5}")

        input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)

def md5_hash_changer_menu():
    """Wrapper untuk menu MD5 changer"""
    changer = MD5HashChanger()
    changer.md5_changer_menu()
