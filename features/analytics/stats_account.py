#!/usr/bin/env python3
"""
Statistik Akun (likes/comments/views growth, engagement rate, best time)
"""

from colorama import Fore, Style
from banner import success_msg, error_msg, info_msg, show_separator
from datetime import datetime, timedelta
import statistics

def show_stats_overview(client, username):
    show_separator()
    print(Fore.CYAN + "\n📈 STATISTIK AKUN" + Style.RESET_ALL)
    show_separator()
    try:
        medias = client.user_medias_v1(client.user_id, amount=30)
        total_likes = sum(m.like_count for m in medias)
        total_comments = sum(m.comment_count for m in medias)
        total_views = sum(getattr(m, 'view_count', 0) for m in medias if hasattr(m, "view_count"))
        post_dates = [datetime.fromtimestamp(m.taken_at.timestamp()) for m in medias]
        post_per_day = len(post_dates) / max(1, (post_dates[0] - post_dates[-1]).days or 1) if len(post_dates) > 1 else 1

        followers = client.user_info_by_username(username).follower_count
        engagement = ((total_likes + total_comments) / (followers * len(medias))) * 100 if followers and medias else 0

        print(Fore.YELLOW + f"\nTotal Likes (30 post terakhir): {Fore.GREEN}{total_likes}")
        print(Fore.YELLOW + f"Total Comments : {Fore.GREEN}{total_comments}")
        print(Fore.YELLOW + f"Total Views (video+reel): {Fore.GREEN}{total_views}")
        print(Fore.YELLOW + f"Followers     : {Fore.GREEN}{followers}")
        print(Fore.YELLOW + f"Jumlah Post   : {Fore.GREEN}{len(medias)}")
        print(Fore.MAGENTA + f"\nEngagement Rate (likes+comments/post/followers): {Fore.CYAN}{engagement:.2f}%")
        print(Fore.GREEN + f"\nPost per hari (rata-rata): {post_per_day:.2f}" + Style.RESET_ALL)

        # Simple Best Time to Post (posting paling banyak interaksi jam berapa)
        hours = [dt.hour for dt in post_dates]
        best_hour = statistics.mode(hours) if hours else None
        if best_hour is not None:
            print(Fore.YELLOW + f"\n⏰ Jam paling aktif interaksi: {Fore.GREEN}{best_hour}:00" + Style.RESET_ALL)

        success_msg("Statistik akun berhasil diambil!\n")
    except Exception as e:
        error_msg(f"Error: {str(e)}")
        input("Tekan Enter untuk kembali...")

