#!/usr/bin/env python3
"""
Account Type Converter
Konversi Personal → Business atau Creator
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import time

class AccountTypeConverter:
    def __init__(self, client):
        self.client = client

    def get_current_account_type(self, username):
        """Cek tipe akun saat ini"""
        try:
            user_info = self.client.user_info_by_username(username)
            
            if user_info.is_business:
                return "BUSINESS"
            elif user_info.is_verified:
                return "VERIFIED"
            else:
                return "PERSONAL"
        
        except Exception as e:
            error_msg(f"Error check type: {str(e)}")
            return None

    def convert_to_creator(self, username):
        """Convert akun ke Creator Account"""
        try:
            info_msg("Converting to Creator Account...")
            
            # Attempt 1: Using set_category (recommended method)
            try:
                self.client.account_change_category(category="creator_athlete")
                success_msg("✅ Account converted to CREATOR!")
                return True
            except:
                pass
            
            # Attempt 2: Using alternative method
            try:
                self.client.account_edit(category="creator_athlete")
                success_msg("✅ Account converted to CREATOR!")
                return True
            except Exception as e:
                error_msg(f"❌ Conversion failed: {str(e)}")
                print(Fore.YELLOW + "\n📝 Kemungkinan penyebab:" + Style.RESET_ALL)
                print("  • Akun belum memenuhi requirement Creator")
                print("  • Perlu minimal followers/engagement")
                print("  • Instagram membatasi konversi dari IP/device baru")
                print("  • Harus convert manual via Instagram app")
                return False
        
        except Exception as e:
            error_msg(f"Error: {str(e)}")
            return False

    def convert_to_business(self, username, email=None, phone=None):
        """Convert akun ke Business Account"""
        try:
            info_msg("Converting to Business Account...")
            print(Fore.YELLOW + "\n⏳ Proses konversi dimulai..." + Style.RESET_ALL)
            print("   (Butuh beberapa menit, jangan ditutup)")
            
            # Business account requires category
            business_categories = [
                "baby_store",
                "beauty",
                "coffee_shop",
                "design_studio",
                "fashion",
                "fitness",
                "photography",
                "restaurant",
                "retail_store",
                "tech",
                "entertainment",
                "food",
                "general"
            ]
            
            print(Fore.YELLOW + "\nPilih kategori bisnis:" + Style.RESET_ALL)
            for i, category in enumerate(business_categories[:10], 1):
                print(f"  {i}. {category.upper()}")
            print("  11. Other")
            
            cat_choice = input(Fore.MAGENTA + "\nPilih kategori (1-11): " + Style.RESET_ALL).strip()
            
            try:
                cat_idx = int(cat_choice) - 1
                if 0 <= cat_idx < len(business_categories):
                    category = business_categories[cat_idx]
                else:
                    category = "general"
            except:
                category = "general"
            
            # Attempt conversion
            try:
                self.client.account_edit(
                    category=category,
                    is_business=True
                )
                success_msg("✅ Account converted to BUSINESS!")
                print(Fore.GREEN + f"   Category: {category.upper()}" + Style.RESET_ALL)
                return True
            except:
                pass
            
            # Alternative: Try dengan data yang lebih lengkap
            try:
                business_name = input(Fore.YELLOW + "\nBusiness name (opsional): " + Style.RESET_ALL).strip()
                
                self.client.account_edit(
                    category=category,
                    is_business=True,
                    name=business_name if business_name else None
                )
                success_msg("✅ Account converted to BUSINESS!")
                return True
            except Exception as e:
                error_msg(f"❌ Conversion failed: {str(e)}")
                print(Fore.YELLOW + "\n📝 Kemungkinan penyebab:" + Style.RESET_ALL)
                print("  • Email belum terverifikasi")
                print("  • Akun baru (< 1 bulan)")
                print("  • Instagram sedang membatasi konversi")
                print("  • Coba manual via Settings > Account > Switch to Professional Account")
                return False
        
        except Exception as e:
            error_msg(f"Error: {str(e)}")
            return False

    def convert_business_to_creator(self, username):
        """Convert Business → Creator Account"""
        try:
            info_msg("Converting Business to Creator...")
            
            self.client.account_change_category(category="creator_athlete")
            success_msg("✅ Account converted BUSINESS → CREATOR!")
            return True
        
        except Exception as e:
            error_msg(f"Error: {str(e)}")
            return False

    def display_conversion_guide(self, current_type):
        """Display guide konversi"""
        show_separator()
        print(Fore.CYAN + "\n📋 ACCOUNT TYPE CONVERSION GUIDE" + Style.RESET_ALL)
        show_separator()
        
        print(Fore.YELLOW + f"\n🔹 Current Type: {current_type}" + Style.RESET_ALL)
        
        if current_type == "PERSONAL":
            print(Fore.YELLOW + "\n✅ Can convert to:" + Style.RESET_ALL)
            print("  • CREATOR (untuk content creator)")
            print("  • BUSINESS (untuk bisnis/brand)")
        
        elif current_type == "CREATOR":
            print(Fore.YELLOW + "\n✅ Can convert to:" + Style.RESET_ALL)
            print("  • BUSINESS (professional)")
        
        elif current_type == "BUSINESS":
            print(Fore.YELLOW + "\n✅ Can convert to:" + Style.RESET_ALL)
            print("  • CREATOR (untuk content creator)")
        
        print(Fore.YELLOW + "\n📝 Requirements:" + Style.RESET_ALL)
        print("  • Akun minimal 30 hari")
        print("  • Email terverifikasi")
        print("  • Nomor telepon terhubung (untuk Business)")
        print("  • Tidak dalam mode restricted")
        print("  • Koneksi internet stabil")

    def run_converter_menu(self, username):
        """Menu account type converter"""
        show_separator()
        print(Fore.CYAN + "\n🔄 ACCOUNT TYPE CONVERTER" + Style.RESET_ALL)
        show_separator()

        try:
            # Get current type
            current_type = self.get_current_account_type(username)
            
            if current_type:
                self.display_conversion_guide(current_type)
                
                print(Fore.YELLOW + "\n🎯 Pilih aksi:" + Style.RESET_ALL)
                
                if current_type == "PERSONAL":
                    print("1. 🎬 Convert to CREATOR")
                    print("2. 🏢 Convert to BUSINESS")
                elif current_type == "CREATOR":
                    print("1. 🏢 Convert to BUSINESS")
                    print("2. 🔙 Convert back to PERSONAL")
                elif current_type == "BUSINESS":
                    print("1. 🎬 Convert to CREATOR")
                    print("2. 🔙 Convert back to PERSONAL")
                
                print("0. ❌ Batal")
                
                choice = input(Fore.MAGENTA + "\nPilih (0-2): " + Style.RESET_ALL).strip()
                
                if choice == '0':
                    info_msg("Dibatalkan")
                    return
                
                elif choice == '1':
                    if current_type == "PERSONAL":
                        confirm = input(Fore.MAGENTA + "\nConvert to CREATOR? (yes/no): " + Style.RESET_ALL).strip().lower()
                        if confirm == "yes":
                            self.convert_to_creator(username)
                    
                    elif current_type == "CREATOR":
                        confirm = input(Fore.MAGENTA + "\nConvert to BUSINESS? (yes/no): " + Style.RESET_ALL).strip().lower()
                        if confirm == "yes":
                            self.convert_to_business(username)
                    
                    elif current_type == "BUSINESS":
                        confirm = input(Fore.MAGENTA + "\nConvert to CREATOR? (yes/no): " + Style.RESET_ALL).strip().lower()
                        if confirm == "yes":
                            self.convert_business_to_creator(username)
                
                elif choice == '2':
                    if current_type in ["CREATOR", "BUSINESS"]:
                        confirm = input(Fore.RED + "\n⚠️  Convert back to PERSONAL? (yes/no): " + Style.RESET_ALL).strip().lower()
                        if confirm == "yes":
                            try:
                                # This might not work via API, user might need to do manually
                                warning_msg("⚠️  Konversi BALIK ke PERSONAL harus manual via Settings > Account")
                                print(Fore.YELLOW + "\nInstruksi:" + Style.RESET_ALL)
                                print("1. Buka Instagram app")
                                print("2. Settings > Account")
                                print("3. Pilih 'Switch to Personal Account'")
                                print("4. Konfirmasi")
                            except Exception as e:
                                error_msg(f"Error: {str(e)}")

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def account_type_converter_menu(client, username):
    """Menu wrapper"""
    converter = AccountTypeConverter(client)
    converter.run_converter_menu(username)
