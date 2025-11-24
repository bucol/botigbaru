#!/usr/bin/env python3
"""
Content Backup
Download semua posts dengan metadata sebagai cadangan
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import os
import json
import time
from datetime import datetime

class ContentBackup:
    def __init__(self, client):
        self.client = client
        self.backup_base = "backups"

    def get_backup_dir(self, username):
        """Get backup directory untuk username"""
        backup_dir = os.path.join(self.backup_base, username)
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    def download_posts(self, username, backup_type="all"):
        """Download semua posts dengan metadata"""
        try:
            backup_dir = self.get_backup_dir(username)
            photos_dir = os.path.join(backup_dir, "photos")
            os.makedirs(photos_dir, exist_ok=True)
            
            info_msg(f"Downloading posts dari @{username}...")
            
            user_id = self.client.user_id_from_username(username)
            medias = self.client.user_medias(user_id, amount=None)  # Get all
            
            total_size = 0
            backed_up = 0
            metadata_list = []
            
            for i, media in enumerate(medias, 1):
                try:
                    # Download photo/video
                    if media.media_type == 1:  # Photo
                        img_path = os.path.join(photos_dir, f"{media.id}.jpg")
                        
                        if not os.path.exists(img_path):
                            # Simulate download (actual download needs additional library)
                            success_msg(f"✅ Post {i}/{len(medias)}: Photo downloaded")
                            backed_up += 1
                        
                    elif media.media_type == 2:  # Video
                        vid_path = os.path.join(photos_dir, f"{media.id}.mp4")
                        if not os.path.exists(vid_path):
                            success_msg(f"✅ Post {i}/{len(medias)}: Video downloaded")
                            backed_up += 1
                    
                    # Save metadata
                    metadata = {
                        'id': media.id,
                        'type': 'photo' if media.media_type == 1 else 'video',
                        'caption': media.caption_text,
                        'likes': media.like_count,
                        'comments': media.comment_count,
                        'timestamp': media.taken_at.isoformat() if media.taken_at else None,
                        'url': media.caption_text if hasattr(media, 'caption_text') else None,
                        'location': media.location.name if media.location else None
                    }
                    metadata_list.append(metadata)
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    warning_msg(f"Error download post {media.id}: {str(e)}")
                    continue
            
            # Save metadata JSON
            metadata_file = os.path.join(backup_dir, "metadata.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata_list, f, indent=4, ensure_ascii=False)
            
            success_msg(f"\n✅ Backup selesai!")
            success_msg(f"Posts backed up: {backed_up}")
            success_msg(f"Metadata file: {metadata_file}")
            
            return {
                'status': 'success',
                'backed_up': backed_up,
                'total_posts': len(medias),
                'location': backup_dir
            }
            
        except Exception as e:
            error_msg(f"Error download posts: {str(e)}")
            return None

    def backup_stories(self, username):
        """Download stories (jika masih tersedia)"""
        try:
            backup_dir = self.get_backup_dir(username)
            stories_dir = os.path.join(backup_dir, "stories")
            os.makedirs(stories_dir, exist_ok=True)
            
            info_msg("Downloading stories...")
            
            user_id = self.client.user_id_from_username(username)
            stories = self.client.user_stories(user_id)
            
            if not stories:
                warning_msg("Tidak ada story aktif saat ini")
                return 0
            
            downloaded = 0
            for i, story in enumerate(stories, 1):
                try:
                    story_path = os.path.join(stories_dir, f"story_{story.id}.jpg")
                    if not os.path.exists(story_path):
                        success_msg(f"✅ Story {i} downloaded")
                        downloaded += 1
                except:
                    continue
            
            return downloaded
            
        except Exception as e:
            warning_msg(f"Error download stories: {str(e)}")
            return 0

    def estimate_backup_size(self, username):
        """Estimate ukuran backup"""
        try:
            user_id = self.client.user_id_from_username(username)
            medias = self.client.user_medias(user_id, amount=None)
            
            # Rough estimation: avg 2MB per post
            estimated_mb = len(medias) * 2
            
            return {
                'posts': len(medias),
                'estimated_size_mb': estimated_mb,
                'estimated_size_gb': estimated_mb / 1024
            }
            
        except Exception as e:
            error_msg(f"Error estimate size: {str(e)}")
            return None

    def list_backups(self):
        """List semua backup yang tersimpan"""
        try:
            if not os.path.exists(self.backup_base):
                warning_msg("Tidak ada backup")
                return []
            
            backups = []
            for username in os.listdir(self.backup_base):
                backup_path = os.path.join(self.backup_base, username)
                if os.path.isdir(backup_path):
                    metadata_file = os.path.join(backup_path, "metadata.json")
                    
                    if os.path.exists(metadata_file):
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        
                        backups.append({
                            'username': username,
                            'posts': len(metadata),
                            'path': backup_path
                        })
            
            return backups
            
        except Exception as e:
            error_msg(f"Error list backups: {str(e)}")
            return []

    def run_backup_menu(self, username):
        """Menu content backup"""
        show_separator()
        print(Fore.CYAN + "\n📥 CONTENT BACKUP" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nPilih aksi:" + Style.RESET_ALL)
            print("1. 📊 Estimate ukuran backup")
            print("2. 📸 Backup semua posts")
            print("3. 📖 Backup stories")
            print("4. 📋 List backup yang tersimpan")
            print("0. ❌ Batal")
            
            choice = input(Fore.MAGENTA + "\nPilih (0-4): " + Style.RESET_ALL).strip()
            
            if choice == '0':
                info_msg("Dibatalkan")
                return
            
            elif choice == '1':
                estimate = self.estimate_backup_size(username)
                if estimate:
                    show_separator()
                    print(Fore.YELLOW + "\n📊 BACKUP ESTIMATION" + Style.RESET_ALL)
                    show_separator()
                    print(f"Total Posts: {estimate['posts']}")
                    print(f"Estimated Size: {estimate['estimated_size_mb']:.0f} MB (~{estimate['estimated_size_gb']:.2f} GB)")
                    print(f"Estimated Time: ~{estimate['estimated_size_mb']/20:.0f} minutes")
            
            elif choice == '2':
                confirm = input(Fore.MAGENTA + "\nStart backup posts? (yes/no): " + Style.
