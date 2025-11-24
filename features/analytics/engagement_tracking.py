#!/usr/bin/env python3
"""
Post dengan engagement tertinggi, hashtag performa, story view analytics
"""

from colorama import Fore, Style
from banner import success_msg, error_msg, info_msg, show_separator

def engagement_menu(client, username):
    show_separator()
    print(Fore.YELLOW + "\n📉 TRACK ENGAGEMENT" + Style.RESET_ALL)
    show_separator()
    print(Fore.GREEN + "1. Post engagement tertinggi")
    print("2. Hashtag performance")
    print("3. Story views analytics")
    print("0. Kembali" + Style.RESET_ALL)
    show_separator()
    choice = input(Fore.MAGENTA + "\nPilih menu engagement (0-3): " + Style.RESET_ALL).strip()
    if choice == "1":
        top_engagement(client, username)
    elif choice == "2":
        hashtag_performance(client, username)
    elif choice == "3":
        story_analytics(client, username)
    elif choice == "0":
        return
    else:
        error_msg("Pilihan tidak valid!")
        input("Tekan Enter untuk kembali...")

def top_engagement(client, username):
    show_separator()
    print(Fore.CYAN + "\nPost dengan Engagement Tertinggi (10 post terakhir):" + Style.RESET_ALL)
    medias = client.user_medias_v1(client.user_id, amount=10)
    if not medias:
        error_msg("Tidak ada post!")
        return
    posts = sorted(
        medias,
        key=lambda m: (m.like_count + m.comment_count),
        reverse=True,
    )
    for m in posts[:3]:
        print(Fore.GREEN + f"- {m.caption_text[:50]}...")
        print(f"  ❤️ {m.like_count} 💬 {m.comment_count}")
    input(Fore.MAGENTA + "\nTekan Enter untuk kembali...")

def hashtag_performance(client, username):
    show_separator()
    print(Fore.CYAN + "\nHashtag Performance (top 10 hashtag post terakhir):" + Style.RESET_ALL)
    medias = client.user_medias_v1(client.user_id, amount=10)
    hashtag_counts = {}
    for m in medias:
        if m.caption_text:
            words = m.caption_text.split()
            hashtags = [w for w in words if w.startswith("#")]
            for h in hashtags:
                hashtag_counts[h] = hashtag_counts.get(h, 0) + 1
    for h, c in sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True):
        print(Fore.YELLOW + f"{h}: {c}x")
    input(Fore.MAGENTA + "\nTekan Enter untuk kembali...")

def story_analytics(client, username):
    show_separator()
    print(Fore.CYAN + "\nStory Views Analytics (7 hari terakhir):" + Style.RESET_ALL)
    try:
        stories = client.user_stories(client.user_id)
        for story in stories:
            print(Fore.GREEN + f"- Story {story.pk}: {story.view_count} views, {story.reel_share_count or 0} shares")
    except Exception:
        print(Fore.RED + "Tidak bisa ambil data story. Akun bukan akun utama atau tidak ada story.")
    input(Fore.MAGENTA + "\nTekan Enter untuk kembali...")
