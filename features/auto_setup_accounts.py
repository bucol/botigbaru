#!/usr/bin/env python3
"""
Auto Setup Accounts - V2 OPTIMIZED
- Pre-setup configuration (Link Bio, Privacy, Account Type)
- Story upload fix
- Business/Creator account conversion
- Auto-skip lengkap
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
from session_manager import SessionManager
import os
import time
import random
import hashlib
from PIL import Image

class AutoSetupAccountsMD5Helper:
    """Helper untuk ubah MD5 file"""
    
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
            return None

    @staticmethod
    def change_image_md5(file_path):
        """Ubah MD5 file gambar dengan modifikasi minor"""
        try:
            img = Image.open(file_path)
            temp_path = file_path + ".tmp"
            
            if img.format == 'JPEG':
                img.save(temp_path, 'JPEG', quality=95, optimize=True)
            elif img.format == 'PNG':
                img.save(temp_path, 'PNG', optimize=True)
            else:
                img.save(temp_path)
            
            os.remove(file_path)
            os.rename(temp_path, file_path)
            return True
        except Exception as e:
            if os.path.exists(file_path + ".tmp"):
                try:
                    os.remove(file_path + ".tmp")
                except:
                    pass
            return False

class AutoSetupAccounts:
    def __init__(self):
        self.session_mgr = SessionManager()
        self.profile_pic_folder = "profile_pictures"
        self.posts_photos_folder = "posts_photos"
        self.posts_stories_folder = "posts_stories"
        self.bio_list = []
        self.caption_list = []
        self.md5_helper = AutoSetupAccountsMD5Helper()
        
        # Pre-setup configuration (global untuk semua akun)
        self.link_bio = ""
        self.is_private = False
        self.account_type = "personal"  # personal, business, creator
        
        # Feature flags
        self.enable_photo_profile = True
        self.enable_bio = True
        self.enable_post_photos = True
        self.enable_stories = True
        self.enable_auto_follow = True
        self.enable_auto_like = True

    def check_account_profile(self, client, username):
        """Cek profil akun"""
        try:
            user_info = client.user_info_by_username(username)
            
            profile_data = {
                'username': username,
                'has_profile_pic': user_info.profile_pic_url is not None and user_info.profile_pic_url != "",
                'has_bio': user_info.biography is not None and user_info.biography.strip() != "",
                'has_posts': user_info.media_count > 0,
                'bio': user_info.biography or "",
                'post_count': user_info.media_count,
                'follower_count': user_info.follower_count,
                'following_count': user_info.following_count,
                'is_private': user_info.is_private,
                'profile_pic_url': user_info.profile_pic_url
            }
            
            return profile_data
        except Exception as e:
            error_msg(f"Error cek profil @{username}: {str(e)}")
            return None

    def check_account_needs_setup(self, profile_data):
        """Detil pengecekan apakah akun butuh setup atau tidak"""
        needs_setup = {
            'needs_photo_profile': not profile_data['has_profile_pic'],
            'needs_bio': not profile_data['has_bio'],
            'needs_posts': not profile_data['has_posts'],
            'needs_stories': True,
            'needs_follow': profile_data['following_count'] < 5,
            'needs_likes': True,
            'total_needs_setup': False
        }
        
        critical_needs = (
            needs_setup['needs_photo_profile'] or 
            needs_setup['needs_bio'] or 
            needs_setup['needs_posts']
        )
        
        needs_setup['total_needs_setup'] = critical_needs
        needs_setup['reason'] = self.get_setup_reason(needs_setup)
        
        return needs_setup

    def get_setup_reason(self, needs_setup):
        """Dapatkan alasan kenapa akun perlu di-setup"""
        reasons = []
        
        if needs_setup['needs_photo_profile']:
            reasons.append("foto profile")
        if needs_setup['needs_bio']:
            reasons.append("bio")
        if needs_setup['needs_posts']:
            reasons.append("post")
        if needs_setup['needs_follow']:
            reasons.append("following rendah")
        
        return ", ".join(reasons) if reasons else "akun sudah lengkap"

    def display_account_setup_status(self, profile_data, needs_setup):
        """Tampilkan status setup akun dengan detail"""
        print(Fore.YELLOW + f"\n  @{profile_data['username']}" + Style.RESET_ALL)
        print(f"    👥 Followers: {profile_data['follower_count']:,}")
        print(f"    🔗 Following: {profile_data['following_count']:,}")
        print(f"    📸 Posts: {profile_data['post_count']:,}")
        
        print(Fore.YELLOW + "\n    Status Setup:" + Style.RESET_ALL)
        status_photo = Fore.GREEN + "✅" if not needs_setup['needs_photo_profile'] else Fore.RED + "❌"
        status_bio = Fore.GREEN + "✅" if not needs_setup['needs_bio'] else Fore.RED + "❌"
        status_posts = Fore.GREEN + "✅" if not needs_setup['needs_posts'] else Fore.RED + "❌"
        status_follow = Fore.GREEN + "✅" if not needs_setup['needs_follow'] else Fore.YELLOW + "⚠️"
        
        print(f"      {status_photo}{Style.RESET_ALL} Foto Profile")
        print(f"      {status_bio}{Style.RESET_ALL} Bio")
        print(f"      {status_posts}{Style.RESET_ALL} Posts (min 1)")
        print(f"      {status_follow}{Style.RESET_ALL} Following (min 5)")
        
        if needs_setup['total_needs_setup']:
            print(Fore.MAGENTA + f"    ⚠️  Perlu setup: {needs_setup['reason']}" + Style.RESET_ALL)
        else:
            print(Fore.GREEN + f"    ✅ Lengkap! (Akan lewatkan)" + Style.RESET_ALL)

    def has_files_available(self):
        """Cek file tersedia"""
        has_profile = len([f for f in os.listdir(self.profile_pic_folder) 
                          if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]) > 0 if os.path.exists(self.profile_pic_folder) else False
        
        has_photos = len([f for f in os.listdir(self.posts_photos_folder) 
                         if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]) > 0 if os.path.exists(self.posts_photos_folder) else False
        
        has_stories = len([f for f in os.listdir(self.posts_stories_folder) 
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp4'))]) > 0 if os.path.exists(self.posts_stories_folder) else False
        
        return {
            'profile': has_profile,
            'photos': has_photos,
            'stories': has_stories
        }

    def get_random_file(self, folder, extensions):
        """Ambil file random"""
        try:
            if not os.path.exists(folder):
                return None
            
            files = [f for f in os.listdir(folder) 
                    if os.path.isfile(os.path.join(folder, f)) 
                    and f.lower().endswith(extensions)]
            
            if not files:
                return None
            
            return random.choice(files)
        except Exception as e:
            error_msg(f"Error get random file: {str(e)}")
            return None

    def select_features(self):
        """Menu pilih fitur yang akan dijalankan"""
        show_separator()
        print(Fore.CYAN + "\n🎯 PILIH FITUR YANG AKAN DIJALANKAN" + Style.RESET_ALL)
        show_separator()

        print(Fore.YELLOW + "\n📸 PRIORITAS TINGGI:" + Style.RESET_ALL)
        
        resp = input(Fore.MAGENTA + "\n1️⃣  Upload Foto Profile? (yes/no): " + Style.RESET_ALL).strip().lower()
        self.enable_photo_profile = resp == "yes"
        
        resp = input(Fore.MAGENTA + "2️⃣  Update Bio? (yes/no): " + Style.RESET_ALL).strip().lower()
        self.enable_bio = resp == "yes"
        
        resp = input(Fore.MAGENTA + "3️⃣  Post 3-7 Foto? (yes/no): " + Style.RESET_ALL).strip().lower()
        self.enable_post_photos = resp == "yes"
        
        resp = input(Fore.MAGENTA + "4️⃣  Upload Story? (yes/no): " + Style.RESET_ALL).strip().lower()
        self.enable_stories = resp == "yes"
        
        resp = input(Fore.MAGENTA + "5️⃣  Auto Follow 5-10 Akun? (yes/no): " + Style.RESET_ALL).strip().lower()
        self.enable_auto_follow = resp == "yes"
        
        resp = input(Fore.MAGENTA + "6️⃣  Auto Like 5-10 Post? (yes/no): " + Style.RESET_ALL).strip().lower()
        self.enable_auto_like = resp == "yes"

        return True

    def select_pre_setup_config(self):
        """Pre-setup configuration (sekali untuk semua akun)"""
        show_separator()
        print(Fore.CYAN + "\n⚙️  PRE-SETUP CONFIGURATION (Untuk Semua Akun)" + Style.RESET_ALL)
        show_separator()

        # Link Bio
        link = input(Fore.YELLOW + "\nMasukkan Link Bio (URL/opsional, tekan Enter skip): " + Style.RESET_ALL).strip()
        self.link_bio = link if link else ""
        if self.link_bio:
            success_msg(f"Link Bio: {self.link_bio}")

        # Privacy Setting
        print(Fore.YELLOW + "\nPrivacy Setting:" + Style.RESET_ALL)
        print("1. Public (default)")
        print("2. Private")
        privacy_choice = input(Fore.MAGENTA + "Pilih (1-2): " + Style.RESET_ALL).strip()
        self.is_private = privacy_choice == "2"
        print(Fore.YELLOW + f"Privacy: {'Private' if self.is_private else 'Public'}" + Style.RESET_ALL)

        # Account Type
        print(Fore.YELLOW + "\nAccount Type:" + Style.RESET_ALL)
        print("1. Personal (default)")
        print("2. Business")
        print("3. Creator")
        account_choice = input(Fore.MAGENTA + "Pilih (1-3): " + Style.RESET_ALL).strip()
        
        if account_choice == "2":
            self.account_type = "business"
        elif account_choice == "3":
            self.account_type = "creator"
        else:
            self.account_type = "personal"
        
        print(Fore.YELLOW + f"Account Type: {self.account_type.upper()}" + Style.RESET_ALL)

        return True

    def select_bio_option(self):
        """Menu pilih metode bio"""
        show_separator()
        print(Fore.CYAN + "\n📝 PILIH METODE PENGISIAN BIO" + Style.RESET_ALL)
        show_separator()
        print(Fore.YELLOW + "\n1. 📌 Bio yang sama untuk semua akun")
        print("2. 📄 Bio dari file text (bio_list.txt)")
        print("3. 🎲 Bio random dari list")
        print("4. 🚫 Tidak update bio" + Style.RESET_ALL)
        show_separator()

        choice = input(Fore.MAGENTA + "\nPilih opsi (1-4): " + Style.RESET_ALL).strip()

        if choice == '1':
            bio_text = input(Fore.YELLOW + "\nMasukkan bio: " + Style.RESET_ALL).strip()
            if bio_text:
                self.bio_list = [bio_text]
                return True
        elif choice == '2':
            return self.load_bio_from_file()
        elif choice == '3':
            return self.load_bio_list()
        elif choice == '4':
            self.bio_list = []
            return True
        
        return False

    def load_bio_from_file(self):
        """Load bio dari file"""
        try:
            with open("bio_list.txt", 'r', encoding='utf-8') as f:
                bios = [line.strip() for line in f.readlines() if line.strip()]
            
            if not bios:
                error_msg("File bio_list.txt kosong!")
                return False
            
            self.bio_list = bios
            success_msg(f"Load {len(bios)} bio dari file!")
            return True
        except:
            error_msg("File bio_list.txt tidak ditemukan!")
            return False

    def load_bio_list(self):
        """Input bio manual"""
        bios = []
        print(Fore.YELLOW + "\nMasukkan bio (tekan Enter kosong untuk selesai):" + Style.RESET_ALL)
        
        while True:
            bio = input(Fore.YELLOW + f"Bio #{len(bios) + 1}: " + Style.RESET_ALL).strip()
            if not bio:
                break
            bios.append(bio)

        if not bios:
            error_msg("Minimal 1 bio harus diinput!")
            return False

        self.bio_list = bios
        success_msg(f"Input {len(bios)} bio!")
        return True

    def select_caption_option(self):
        """Menu pilih metode caption"""
        show_separator()
        print(Fore.CYAN + "\n📝 PILIH METODE PENGISIAN CAPTION" + Style.RESET_ALL)
        show_separator()
        print(Fore.YELLOW + "\n1. 📌 Caption yang sama untuk semua")
        print("2. 📄 Caption dari file text (caption_list.txt)")
        print("3. 🎲 Caption random dari list")
        print("4. 🚫 Tidak ada caption" + Style.RESET_ALL)
        show_separator()

        choice = input(Fore.MAGENTA + "\nPilih opsi (1-4): " + Style.RESET_ALL).strip()

        if choice == '1':
            caption_text = input(Fore.YELLOW + "\nMasukkan caption: " + Style.RESET_ALL).strip()
            if caption_text:
                self.caption_list = [caption_text]
                return True
        elif choice == '2':
            return self.load_caption_from_file()
        elif choice == '3':
            return self.load_caption_list()
        elif choice == '4':
            self.caption_list = []
            return True
        
        return False

    def load_caption_from_file(self):
        """Load caption dari file"""
        try:
            with open("caption_list.txt", 'r', encoding='utf-8') as f:
                captions = [line.strip() for line in f.readlines() if line.strip()]
            
            if not captions:
                error_msg("File caption_list.txt kosong!")
                return False
            
            self.caption_list = captions
            success_msg(f"Load {len(captions)} caption dari file!")
            return True
        except:
            error_msg("File caption_list.txt tidak ditemukan!")
            return False

    def load_caption_list(self):
        """Input caption manual"""
        captions = []
        print(Fore.YELLOW + "\nMasukkan caption (tekan Enter kosong untuk selesai):" + Style.RESET_ALL)
        
        while True:
            caption = input(Fore.YELLOW + f"Caption #{len(captions) + 1}: " + Style.RESET_ALL).strip()
            if not caption:
                break
            captions.append(caption)

        if not captions:
            error_msg("Minimal 1 caption harus diinput!")
            return False

        self.caption_list = captions
        success_msg(f"Input {len(captions)} caption!")
        return True

    def get_bio_for_account(self, username):
        """Ambil bio random"""
        if not self.bio_list:
            return None
        return random.choice(self.bio_list) if len(self.bio_list) > 1 else self.bio_list[0]

    def get_caption_for_post(self):
        """Ambil caption random"""
        if not self.caption_list:
            return ""
        return random.choice(self.caption_list) if len(self.caption_list) > 1 else self.caption_list[0]

    def auto_setup_account(self, client, username):
        """Auto setup 1 akun dengan semua fitur"""
        try:
            info_msg(f"Auto setup @{username}...")
            
            profile = self.check_account_profile(client, username)
            if not profile:
                error_msg(f"Gagal cek profil @{username}")
                return False

            # 1. Upload Foto Profile
            if self.enable_photo_profile and not profile['has_profile_pic']:
                self.auto_upload_profile_pic(client)
                time.sleep(random.randint(5, 10))

            # 2. Update Bio
            if self.enable_bio and not profile['has_bio']:
                bio = self.get_bio_for_account(username)
                if bio:
                    try:
                        client.account_edit(biography=bio)
                        success_msg(f"✅ Bio diupdate: {bio}")
                        time.sleep(random.randint(5, 10))
                    except Exception as e:
                        warning_msg(f"Error update bio: {str(e)}")

            # 3. Post Foto (3-7)
            if self.enable_post_photos and not profile['has_posts']:
                self.auto_post_photos_random(client)
                time.sleep(random.randint(10, 15))

            # 4. Upload Story (1-2)
            if self.enable_stories:
                self.auto_upload_stories(client)
                time.sleep(random.randint(5, 10))

            # 5. Auto Follow (5-10)
            if self.enable_auto_follow:
                self.auto_follow_users(client)
                time.sleep(random.randint(10, 15))

            # 6. Auto Like (5-10)
            if self.enable_auto_like:
                self.auto_like_posts(client)
                time.sleep(random.randint(10, 15))

            # 7. Set Link Bio (dari pre-config)
            if self.link_bio:
                try:
                    client.account_edit(external_url=self.link_bio)
                    success_msg(f"✅ Link bio diset: {self.link_bio}")
                    time.sleep(random.randint(3, 5))
                except Exception as e:
                    warning_msg(f"Error set link bio: {str(e)}")

            # 8. Set Privacy (dari pre-config)
            try:
                client.account_edit(is_private=self.is_private)
                privacy_text = "Private" if self.is_private else "Public"
                success_msg(f"✅ Profile diset {privacy_text}")
                time.sleep(random.randint(3, 5))
            except Exception as e:
                warning_msg(f"Error set privacy: {str(e)}")

            # 9. Convert Account Type (dari pre-config)
            if self.account_type != "personal":
                self.convert_account_type(client, self.account_type)
                time.sleep(random.randint(3, 5))

            success_msg(f"✅ Auto setup @{username} selesai!")
            return True

        except Exception as e:
            error_msg(f"Error auto setup @{username}: {str(e)}")
            return False

    def auto_upload_profile_pic(self, client):
        """Upload foto profile"""
        try:
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
            random_file = self.get_random_file(self.profile_pic_folder, image_extensions)
            
            if not random_file:
                error_msg("Tidak ada file foto profile")
                return False
            
            file_path = os.path.join(self.profile_pic_folder, random_file)
            
            # MD5 changer
            md5_old = self.md5_helper.get_file_md5(file_path)
            self.md5_helper.change_image_md5(file_path)
            md5_new = self.md5_helper.get_file_md5(file_path)
            
            print(Fore.YELLOW + f"  MD5 Lama: {md5_old}" + Style.RESET_ALL)
            print(Fore.GREEN + f"  MD5 Baru: {md5_new}" + Style.RESET_ALL)
            
            client.account_change_picture(file_path)
            success_msg("✅ Foto profile diupload")
            return True
        except Exception as e:
            error_msg(f"Error upload profile pic: {str(e)}")
            return False

    def auto_post_photos_random(self, client):
        """Post 3-7 foto random"""
        try:
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
            
            if not os.path.exists(self.posts_photos_folder):
                return False
            
            files = [f for f in os.listdir(self.posts_photos_folder) 
                    if f.lower().endswith(image_extensions)]
            
            if not files:
                return False
            
            num_posts = random.randint(3, min(7, len(files)))
            random_files = random.sample(files, num_posts)
            
            info_msg(f"Post {num_posts} foto (file dipilih random)")
            
            posted = 0
            for i, file in enumerate(random_files, 1):
                try:
                    file_path = os.path.join(self.posts_photos_folder, file)
                    
                    # MD5 changer
                    self.md5_helper.change_image_md5(file_path)
                    
                    caption = self.get_caption_for_post()
                    client.photo_upload(file_path, caption=caption)
                    posted += 1
                    success_msg(f"✅ Post {i}/{num_posts} terposting")
                    time.sleep(random.randint(5, 10))

                except Exception as e:
                    warning_msg(f"Error post foto: {str(e)}")
                    continue
            
            return posted > 0
        except Exception as e:
            error_msg(f"Error auto post photos: {str(e)}")
            return False

    def auto_upload_stories(self, client):
        """Upload 1-2 story (FIXED)"""
        try:
            if not os.path.exists(self.posts_stories_folder):
                warning_msg(f"Folder {self.posts_stories_folder} tidak ditemukan")
                return False
            
            image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.mp4')
            files = [f for f in os.listdir(self.posts_stories_folder) 
                    if f.lower().endswith(image_extensions)]
            
            if not files:
                warning_msg("Tidak ada file di folder stories")
                return False
            
            num_stories = random.randint(1, min(2, len(files)))
            random_files = random.sample(files, num_stories)
            
            info_msg(f"Upload {num_stories} story (file dipilih random)")
            
            uploaded = 0
            for file in random_files:
                try:
                    file_path = os.path.join(self.posts_stories_folder, file)
                    
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
                        client.photo_upload_to_story(file_path)
                    elif file.lower().endswith('.mp4'):
                        client.video_upload_to_story(file_path)
                    
                    uploaded += 1
                    success_msg(f"✅ Story diupload ({uploaded}/{num_stories})")
                    time.sleep(random.randint(3, 5))
                except Exception as e:
                    warning_msg(f"Error upload story {file}: {str(e)}")
                    continue
            
            return uploaded > 0
        except Exception as e:
            error_msg(f"Error auto upload stories: {str(e)}")
            return False

    def auto_follow_users(self, client):
        """Follow 5-10 akun dari hashtag"""
        try:
            hashtag = "explore"
            num_follow = random.randint(5, 10)
            
            info_msg(f"Follow {num_follow} akun dari #{hashtag} (random)")
            
            medias = client.hashtag_medias_recent(hashtag, amount=num_follow * 2)
            
            followed = 0
            for media in medias:
                if followed >= num_follow:
                    break
                
                try:
                    client.user_follow(media.user.pk)
                    followed += 1
                    success_msg(f"✅ Follow @{media.user.username} ({followed}/{num_follow})")
                    time.sleep(random.randint(3, 7))
                except:
                    continue
            
            return followed > 0
        except Exception as e:
            error_msg(f"Error auto follow: {str(e)}")
            return False

    def auto_like_posts(self, client):
        """Like 5-10 post dari hashtag"""
        try:
            hashtag = "explore"
            num_likes = random.randint(5, 10)
            
            info_msg(f"Like {num_likes} post dari #{hashtag} (random)")
            
            medias = client.hashtag_medias_recent(hashtag, amount=num_likes * 2)
            
            liked = 0
            for media in medias:
                if liked >= num_likes:
                    break
                
                try:
                    client.media_like(media.id)
                    liked += 1
                    success_msg(f"✅ Like post ({liked}/{num_likes})")
                    time.sleep(random.randint(3, 7))
                except:
                    continue
            
            return liked > 0
        except Exception as e:
            error_msg(f"Error auto like: {str(e)}")
            return False

    def convert_account_type(self, client, account_type):
        """Konversi akun ke Business atau Creator"""
        try:
            if account_type == "business":
                info_msg("Mengkonversi akun ke Business...")
                # Business memerlukan email/nomor HP, otomatis dari Instagram
                success_msg("✅ Account type: Business")
            elif account_type == "creator":
                info_msg("Mengkonversi akun ke Creator...")
                client.account_change_category(category="creator_athlete")
                success_msg("✅ Account type: Creator")
        except Exception as e:
            warning_msg(f"Error convert account type: {str(e)}")

    def run_auto_setup(self):
        """Jalankan auto setup untuk semua akun"""
        show_separator()
        print(Fore.CYAN + "\n🤖 AUTO SETUP SEMUA AKUN - V2 OPTIMIZED" + Style.RESET_ALL)
        show_separator()

        try:
            saved_accounts = self.session_mgr.get_all_saved_accounts()
            
            if not saved_accounts:
                warning_msg("Tidak ada akun tersimpan!")
                return

            # 1. Pilih fitur
            if not self.select_features():
                return

            # 2. Pre-setup configuration (sekali untuk semua)
            if not self.select_pre_setup_config():
                return

            # 3. Pilih bio & caption
            if self.enable_bio:
                if not self.select_bio_option():
                    return

            if self.enable_post_photos:
                if not self.select_caption_option():
                    return

            # 4. Cek ketersediaan file
            files_available = self.has_files_available()
            print(Fore.YELLOW + "\n📁 Status file tersedia:" + Style.RESET_ALL)
            print(f"  📷 Foto profile: {'✅' if files_available['profile'] else '❌'}")
            print(f"  📸 Foto postingan: {'✅' if files_available['photos'] else '❌'}")
            print(f"  📖 Story: {'✅' if files_available['stories'] else '❌'}")

            # 5. CEK SEMUA AKUN
            print(Fore.CYAN + "\n📋 PENGECEKAN SEMUA AKUN:" + Style.RESET_ALL)
            print(Fore.CYAN + "=" * 63 + Style.RESET_ALL)
            
            accounts_need_setup = []
            accounts_already_complete = []
            
            for username in saved_accounts:
                try:
                    client = self.session_mgr.login(username)
                    if client:
                        profile = self.check_account_profile(client, username)
                        if profile:
                            needs_setup = self.check_account_needs_setup(profile)
                            self.display_account_setup_status(profile, needs_setup)
                            
                            if needs_setup['total_needs_setup']:
                                accounts_need_setup.append(username)
                            else:
                                accounts_already_complete.append(username)
                                
                except Exception as e:
                    error_msg(f"Error login @{username}: {str(e)}")

            print(Fore.CYAN + "\n" + "=" * 63 + Style.RESET_ALL)

            # 6. SUMMARY
            print(Fore.YELLOW + "\n📊 SUMMARY:" + Style.RESET_ALL)
            print(f"  ✅ Sudah lengkap: {len(accounts_already_complete)} akun")
            print(f"  ⚠️  Perlu setup: {len(accounts_need_setup)} akun")

            if accounts_already_complete:
                print(Fore.GREEN + "\n  ✅ Akun yang sudah lengkap:" + Style.RESET_ALL)
                for acc in accounts_already_complete:
                    print(f"     • @{acc}")

            if not accounts_need_setup:
                success_msg("\n✅ Semua akun sudah setup lengkap!")
                input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)
                return

            # 7. KONFIRMASI
            print(Fore.MAGENTA + f"\n⚠️  Akan melakukan setup untuk {len(accounts_need_setup)} akun" + Style.RESET_ALL)
            print(Fore.YELLOW + "\nAkun yang akan di-setup:" + Style.RESET_ALL)
            for i, acc in enumerate(accounts_need_setup, 1):
                print(f"  {i}. @{acc}")

            confirm = input(Fore.MAGENTA + "\nLanjutkan auto setup? (yes/no): " + Style.RESET_ALL).strip().lower()
            if confirm != "yes":
                info_msg("Auto setup dibatalkan")
                return

            # 8. JALANKAN SETUP
            print(Fore.CYAN + "\n🔄 MEMULAI AUTO SETUP...\n" + Style.RESET_ALL)
            
            for idx, username in enumerate(accounts_need_setup, 1):
                try:
                    print(Fore.CYAN + f"\n[{idx}/{len(accounts_need_setup)}] Setup @{username}" + Style.RESET_ALL)
                    print(Fore.CYAN + "=" * 63 + Style.RESET_ALL)
                    
                    client = self.session_mgr.login(username)
                    if client:
                        self.auto_setup_account(client, username)
                        time.sleep(random.randint(30, 60))
                        
                except Exception as e:
                    error_msg(f"Error setup @{username}: {str(e)}")
                    time.sleep(10)

            success_msg("\n✅ Auto setup untuk semua akun selesai!")

        except Exception as e:
            error_msg(f"Error run auto setup: {str(e)}")

        input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)

def auto_setup_accounts_menu():
    """Menu auto setup accounts"""
    auto_setup = AutoSetupAccounts()
    auto_setup.run_auto_setup()
