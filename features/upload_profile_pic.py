#!/usr/bin/env python3
"""
Upload Foto Profil Instagram
Scan folder profile_pictures, pilih file, auto ubah MD5, lalu upload
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import os
import hashlib
from PIL import Image

class ProfilePicMD5Helper:
    """Helper untuk ubah MD5 foto profile"""
    
    @staticmethod
    def get_file_md5(file_path):
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

    @staticmethod
    def change_image_md5(file_path):
        """Ubah MD5 file gambar dengan modifikasi minor"""
        try:
            img = Image.open(file_path)
            
            # Ubah quality dengan variation
            temp_path = file_path + ".tmp"
            
            if img.format == 'JPEG':
                img.save(temp_path, 'JPEG', quality=95, optimize=True)
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
                try:
                    os.remove(file_path + ".tmp")
                except:
                    pass
            return False

def upload_profile_picture(client):
    """Upload foto profil dengan auto MD5 changer"""
    show_separator()
    print(Fore.CYAN + "\n📷 UPLOAD FOTO PROFIL" + Style.RESET_ALL)
    show_separator()

    try:
        # Tentukan folder profile pictures
        profile_pic_folder = "profile_pictures"
        
        # Cek apakah folder ada
        if not os.path.exists(profile_pic_folder):
            warning_msg(f"Folder '{profile_pic_folder}' tidak ditemukan!")
            info_msg("Membuat folder baru...")
            os.makedirs(profile_pic_folder)
            warning_msg(f"Silakan masukkan file foto ke folder '{profile_pic_folder}' dan coba lagi")
            return

        # Scan file di folder (hanya file gambar)
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
        image_files = [f for f in os.listdir(profile_pic_folder) 
                       if os.path.isfile(os.path.join(profile_pic_folder, f)) 
                       and f.lower().endswith(image_extensions)]

        if not image_files:
            warning_msg(f"Tidak ada file gambar di folder '{profile_pic_folder}'")
            info_msg(f"Format gambar yang didukung: {', '.join(image_extensions)}")
            return

        # Tampilkan daftar file
        image_files.sort()
        print(Fore.GREEN + f"\n📁 File foto yang ditemukan di folder '{profile_pic_folder}':" + Style.RESET_ALL)
        for i, filename in enumerate(image_files, 1):
            file_path = os.path.join(profile_pic_folder, filename)
            file_size = os.path.getsize(file_path) / 1024  # Size dalam KB
            print(Fore.YELLOW + f"  {i}. {filename} ({file_size:.2f} KB)" + Style.RESET_ALL)

        print(Fore.CYAN + f"  0. Batal" + Style.RESET_ALL)
        show_separator()

        # Minta user pilih file
        choice = input(Fore.MAGENTA + f"\nPilih foto (0-{len(image_files)}): " + Style.RESET_ALL).strip()
        
        try:
            choice_num = int(choice)
            if choice_num == 0:
                info_msg("Upload dibatalkan")
                return
            elif choice_num < 1 or choice_num > len(image_files):
                error_msg("Pilihan tidak valid!")
                return
        except ValueError:
            error_msg("Input harus angka!")
            return

        # Ambil file yang dipilih
        selected_file = image_files[choice_num - 1]
        file_path = os.path.join(profile_pic_folder, selected_file)

        # Validasi ukuran file (Instagram limit biasanya 8MB)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 8:
            error_msg(f"Ukuran file terlalu besar! ({file_size_mb:.2f} MB, max 8 MB)")
            return

        # Konfirmasi sebelum upload
        print(Fore.YELLOW + f"\n📸 File yang akan diupload: {selected_file}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"   Ukuran: {file_size_mb:.2f} MB" + Style.RESET_ALL)
        
        confirm = input(Fore.MAGENTA + "\n⚠️  Lanjutkan upload? (yes/no): " + Style.RESET_ALL).strip().lower()
        if confirm != "yes":
            info_msg("Upload dibatalkan")
            return

        # ===== MD5 HASH CHANGER =====
        print(Fore.CYAN + "\n" + "="*63)
        print("🔐 MD5 HASH CHANGER - AUTO UBAH MD5 SEBELUM UPLOAD")
        print("="*63 + Style.RESET_ALL)

        md5_helper = ProfilePicMD5Helper()

        # Hitung MD5 sebelum ubah
        md5_old = md5_helper.get_file_md5(file_path)
        print(Fore.YELLOW + f"\n📄 File: {selected_file}" + Style.RESET_ALL)
        print(Fore.RED + f"❌ MD5 Lama: {md5_old}" + Style.RESET_ALL)

        # Ubah MD5
        info_msg("Mengubah MD5 file...")
        if md5_helper.change_image_md5(file_path):
            md5_new = md5_helper.get_file_md5(file_path)
            print(Fore.GREEN + f"✅ MD5 Baru: {md5_new}" + Style.RESET_ALL)
            success_msg("MD5 berhasil diubah!")
        else:
            warning_msg("Gagal ubah MD5, lanjutkan dengan file asli...")
            md5_new = md5_old

        # ===== UPLOAD FOTO =====
        print(Fore.CYAN + "\n" + "="*63)
        print("📷 UPLOAD FOTO PROFILE")
        print("="*63 + Style.RESET_ALL)

        info_msg("Mengupload foto profil...")
        
        client.account_change_picture(file_path)

        success_msg(f"Foto profil berhasil diubah! 🎉")
        print(Fore.GREEN + f"\n✅ Upload Berhasil" + Style.RESET_ALL)
        print(Fore.YELLOW + f"   File: {selected_file}" + Style.RESET_ALL)
        print(Fore.YELLOW + f"   Ukuran: {file_size_mb:.2f} MB" + Style.RESET_ALL)
        print(Fore.GREEN + f"   MD5 Baru: {md5_new}" + Style.RESET_ALL)

    except Exception as e:
        error_msg(f"Error saat upload foto profil: {str(e)}")
        warning_msg("Pastikan:")
        warning_msg("  - File gambar valid (JPG, PNG, GIF, BMP)")
        warning_msg("  - Ukuran file tidak lebih dari 8 MB")
        warning_msg("  - Koneksi internet stabil")

    input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)
