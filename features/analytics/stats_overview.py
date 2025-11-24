#!/usr/bin/env python3
"""
Analytics & Monitoring - Enhanced
Tambahan: Engagement Heatmap, Post Reach, Story Viewers
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style

def analytics_menu(client, username):
    """Menu analytics dengan fitur lengkap"""
    while True:
        show_separator()
        print(Fore.CYAN + f"\n📊 ANALYTICS & MONITORING - @{username}" + Style.RESET_ALL)
        show_separator()
        print(Fore.YELLOW + "\n1. 📈 Overview Stats")
        print("2. 🔥 Engagement Heatmap")
        print("3. 👁️  Post Reach & Impressions")
        print("4. 📖 Story Viewers Analysis")
        print("5. 📊 Detailed Report")
        print("0. ❌ Kembali" + Style.RESET_ALL)
        show_separator()

        choice = input(Fore.MAGENTA + "\nPilih menu (0-5): " + Style.RESET_ALL).strip()

        if choice == '0':
            info_msg("Kembali...")
            break
        elif choice == '1':
            show_overview_stats(client, username)
        elif choice == '2':
            show_engagement_heatmap(client, username)
        elif choice == '3':
            show_post_reach_impressions(client, username)
        elif choice == '4':
            show_story_viewers_analysis(client, username)
        elif choice == '5':
            show_detailed_report(client, username)
        else:
            error_msg("Pilihan tidak valid!")

        input(Fore.CYAN + "\nTekan Enter untuk lanjut..." + Style.RESET_ALL)

def show_overview_stats(client, username):
    """Tampilkan overview stats akun"""
    try:
        info_msg("Mengambil data stats...")
        user_info = client.user_info_by_username(username)
        
        show_separator()
        print(Fore.GREEN + f"\n📊 OVERVIEW STATS - @{username}" + Style.RESET_ALL)
        show_separator()
        print(f"👥 Followers: {user_info.follower_count:,}")
        print(f"👤 Following: {user_info.following_count:,}")
        print(f"📸 Total Posts: {user_info.media_count:,}")
        print(f"📝 Bio: {user_info.biography}")
        
        if user_info.external_url:
            print(f"🔗 Link: {user_info.external_url}")
        
        success_msg("\n✅ Data berhasil dimuat!")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def show_engagement_heatmap(client, username):
    """Visualisasi waktu terbaik untuk posting"""
    try:
        info_msg("Menganalisis engagement pattern...")
        
        user_id = client.user_id_from_username(username)
        medias = client.user_medias(user_id, amount=50)
        
        # Analisis waktu posting dan engagement
        hour_engagement = {}
        for media in medias:
            hour = media.taken_at.hour
            likes = media.like_count
            comments = media.comment_count
            engagement = likes + (comments * 2)
            
            if hour not in hour_engagement:
                hour_engagement[hour] = []
            hour_engagement[hour].append(engagement)
        
        # Hitung rata-rata engagement per jam
        avg_engagement = {}
        for hour, engagements in hour_engagement.items():
            avg_engagement[hour] = sum(engagements) / len(engagements)
        
        # Sort by engagement
        sorted_hours = sorted(avg_engagement.items(), key=lambda x: x[1], reverse=True)
        
        show_separator()
        print(Fore.GREEN + "\n🔥 ENGAGEMENT HEATMAP (Waktu Terbaik Posting)" + Style.RESET_ALL)
        show_separator()
        print(Fore.YELLOW + "\nTop 5 Waktu Terbaik:" + Style.RESET_ALL)
        for i, (hour, engagement) in enumerate(sorted_hours[:5], 1):
            print(f"{i}. Jam {hour:02d}:00 - Avg Engagement: {engagement:.0f}")
        
        success_msg("\n✅ Analisis selesai!")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def show_post_reach_impressions(client, username):
    """Tampilkan reach & impressions post terbaru"""
    try:
        info_msg("Mengambil data reach & impressions...")
        
        user_id = client.user_id_from_username(username)
        medias = client.user_medias(user_id, amount=10)
        
        show_separator()
        print(Fore.GREEN + "\n👁️  POST REACH & IMPRESSIONS (10 Post Terbaru)" + Style.RESET_ALL)
        show_separator()
        
        for i, media in enumerate(medias, 1):
            print(f"\n{i}. Post ID: {media.id}")
            print(f"   ❤️  Likes: {media.like_count:,}")
            print(f"   💬 Comments: {media.comment_count:,}")
            print(f"   👁️  Views: {media.view_count:,}" if media.view_count else "   👁️  Views: N/A")
            
            # Hitung engagement rate
            engagement = media.like_count + media.comment_count
            print(f"   📊 Total Engagement: {engagement:,}")
        
        success_msg("\n✅ Data berhasil dimuat!")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def show_story_viewers_analysis(client, username):
    """Analisis story viewers"""
    try:
        info_msg("Mengambil data story viewers...")
        
        # Ambil story terbaru
        stories = client.user_stories(client.user_id_from_username(username))
        
        if not stories:
            warning_msg("Tidak ada story aktif saat ini")
            return
        
        show_separator()
        print(Fore.GREEN + f"\n📖 STORY VIEWERS ANALYSIS" + Style.RESET_ALL)
        show_separator()
        print(f"Total Stories Aktif: {len(stories)}")
        
        total_views = 0
        for i, story in enumerate(stories, 1):
            viewers_count = story.viewer_count if hasattr(story, 'viewer_count') else 0
            total_views += viewers_count
            print(f"\n{i}. Story {story.id}")
            print(f"   👁️  Views: {viewers_count:,}")
        
        print(f"\n📊 Total Views Semua Story: {total_views:,}")
        success_msg("\n✅ Analisis selesai!")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

def show_detailed_report(client, username):
    """Laporan lengkap analytics"""
    try:
        info_msg("Membuat laporan lengkap...")
        
        user_info = client.user_info_by_username(username)
        user_id = client.user_id_from_username(username)
        medias = client.user_medias(user_id, amount=50)
        
        # Hitung statistik
        total_likes = sum(m.like_count for m in medias)
        total_comments = sum(m.comment_count for m in medias)
        avg_likes = total_likes / len(medias) if medias else 0
        avg_comments = total_comments / len(medias) if medias else 0
        
        show_separator()
        print(Fore.GREEN + f"\n📊 DETAILED ANALYTICS REPORT - @{username}" + Style.RESET_ALL)
        show_separator()
        
        print(Fore.YELLOW + "\n👤 ACCOUNT INFO:" + Style.RESET_ALL)
        print(f"   Followers: {user_info.follower_count:,}")
        print(f"   Following: {user_info.following_count:,}")
        print(f"   Posts: {user_info.media_count:,}")
        
        print(Fore.YELLOW + "\n📈 ENGAGEMENT (50 Post Terbaru):" + Style.RESET_ALL)
        print(f"   Total Likes: {total_likes:,}")
        print(f"   Total Comments: {total_comments:,}")
        print(f"   Avg Likes per Post: {avg_likes:.0f}")
        print(f"   Avg Comments per Post: {avg_comments:.0f}")
        
        # Engagement rate
        if user_info.follower_count > 0:
            engagement_rate = ((total_likes + total_comments) / (len(medias) * user_info.follower_count)) * 100
            print(f"   Engagement Rate: {engagement_rate:.2f}%")
        
        success_msg("\n✅ Laporan lengkap berhasil dibuat!")

    except Exception as e:
        error_msg(f"Error: {str(e)}")
