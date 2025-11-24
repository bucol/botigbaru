#!/usr/bin/env python3
"""
Bulk Delete Posts
Hapus banyak postingan sekaligus berdasarkan kriteria
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
from datetime import datetime, timedelta
import time

class BulkDeletePosts:
    def __init__(self, client):
        self.client = client

    def get_posts_by_criteria(self, client, username, criteria_type, criteria_value):
        """Get posts berdasarkan kriteria"""
        try:
            user_id = client.user_id_from_username(username)
            medias = client.user_medias(user_id, amount=None)

            filtered = []

            if criteria_type == "engagement":
                # Delete posts dengan likes < threshold
                threshold = int(criteria_value)
                filtered = [m for m in medias if m.like_count < threshold]

            elif criteria_type == "date_range":
                # Delete posts antara date range
                dates = criteria_value.split(",")
                if len(dates) != 2:
                    error_msg("Format: YYYY-MM-DD,YYYY-MM-DD")
                    return None
                
                try:
                    start_date = datetime.strptime(dates[0].strip(), "%Y-%m-%d")
                    end_date = datetime.strptime(dates[1].strip(), "%Y-%m-%d")
                except ValueError:
                    error_msg("Format tanggal salah!")
                    return None

                filtered = [m for m in medias if start_date <= m.taken_at <= end_date]

            elif criteria_type == "caption":
                # Delete posts dengan caption mengandung keyword
                keyword = criteria_value.lower()
                filtered = [m for m in medias if keyword in (m.caption_text or "").lower()]

            elif criteria_type == "media_type":
                # Delete by media type (photo/video)
                media_type = criteria_value.lower()
                if media_type == "photo":
                    filtered = [m for m in medias if m.media_type == 1]
                elif media_type == "video":
                    filtered = [m for m in medias if m.media_type == 2]
                elif media_type == "carousel":
                    filtered = [m for m in medias if m.media_type == 8]

            return filtered

        except Exception as e:
            error_msg(f"Error filter posts: {str(e)}")
            return None

    def preview_delete(self, posts):
        """Preview posts yang akan dihapus"""
        if not posts:
            warning_msg("Tidak ada posts yang match kriteria")
            return False

        show_separator()
        print(Fore.YELLOW + f"\n📋 PREVIEW - {len(posts)} Posts yang akan dihapus:" + Style.RESET_ALL)
        show_separator()

        for i, post in enumerate(posts[:10], 1):  # Show max 10
            media_type = "Photo" if post.media_type == 1 else "Video" if post.media_type == 2 else "Carousel"
            print(f"\n{i}. [{media_type}] ID: {post.id}")
            print(f"   Likes: {post.like_count} | Comments: {post.comment_count}")
            if post.caption_text:
                caption = post.caption_text[:50] + "..." if len(post.caption_text) > 50 else post.caption_text
                print(f"   Caption: {caption}")

        if len(posts) > 10:
            print(f"\n... dan {len(posts) - 10} post lainnya")

        print(Fore.RED + f"\n⚠️  TOTAL DELETE: {len(posts)} posts" + Style.RESET_ALL)

        confirm = input(Fore.RED + "\nBenarkah ingin menghapus? (yes/no): " + Style.RESET_ALL).strip().lower()

        return confirm == "yes"

    def delete_posts_batch(self, client, posts, delay=5):
        """Delete posts dengan batch processing"""
        try:
            deleted = 0
            failed = 0

            info_msg(f"Deleting {len(posts)} posts...")

            for i, post in enumerate(posts, 1):
                try:
                    client.media_delete(post.id)
                    deleted += 1
                    success_msg(f"✅ Deleted {i}/{len(posts)}")
                    time.sleep(delay)

                except Exception as e:
                    failed += 1
                    warning_msg(f"Error delete post {post.id}: {str(e)}")
                    time.sleep(2)

            show_separator()
            print(Fore.GREEN + f"\n✅ DELETION COMPLETE" + Style.RESET_ALL)
            print(f"  Deleted: {deleted}")
            print(f"  Failed: {failed}")
            print(f"  Total: {len(posts)}")

            return True

        except Exception as e:
            error_msg(f"Error batch delete: {str(e)}")
            return False

    def run_delete_menu(self, username):
        """Menu bulk delete"""
        show_separator()
        print(Fore.CYAN + "\n🗑️  BULK DELETE POSTS" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nPilih kriteria delete:" + Style.RESET_ALL)
            print("1. 💬 By engagement (likes < threshold)")
            print("2. 📅 By date range (YYYY-MM-DD,YYYY-MM-DD)")
            print("3. 🔤 By caption keyword")
            print("4. 📸 By media type (photo/video/carousel)")
            print("0. ❌ Batal")

            choice = input(Fore.MAGENTA + "\nPilih (0-4): " + Style.RESET_ALL).strip()

            criteria_map = {
                '1': ('engagement', 'Masukkan threshold likes: '),
                '2': ('date_range', 'Masukkan range (start,end): '),
                '3': ('caption', 'Masukkan keyword: '),
                '4': ('media_type', 'Pilih type (photo/video/carousel): ')
            }

            if choice == '0':
                info_msg("Dibatalkan")
                return

            if choice not in criteria_map:
                error_msg("Pilihan tidak valid!")
                return

            criteria_type, prompt = criteria_map[choice]
            criteria_value = input(Fore.YELLOW + f"\n{prompt}" + Style.RESET_ALL).strip()

            if not criteria_value:
                error_msg("Value tidak boleh kosong!")
                return

            # Get posts
            info_msg("Fetching posts...")
            posts = self.get_posts_by_criteria(self.client, username, criteria_type, criteria_value)

            if posts is None or len(posts) == 0:
                warning_msg("Tidak ada posts yang match")
                return

            # Preview
            if self.preview_delete(posts):
                delay = input(Fore.YELLOW + "\nDelay antar delete (detik, default: 5): " + Style.RESET_ALL).strip()
                delay = int(delay) if delay else 5

                self.delete_posts_batch(self.client, posts, delay)
            else:
                info_msg("Dibatalkan")

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def bulk_delete_menu(client, username):
    """Menu wrapper"""
    delete = BulkDeletePosts(client)
    delete.run_delete_menu(username)
