#!/usr/bin/env python3
"""
Enhanced Engagement Analytics
Analisis lengkap performa engagement dengan trend & insights
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import json
import os
from datetime import datetime, timedelta

class EngagementAnalyticsEnhanced:
    def __init__(self, client):
        self.client = client
        self.analytics_dir = "analytics"
        os.makedirs(self.analytics_dir, exist_ok=True)

    def analyze_engagement(self, username):
        """Analisis engagement dengan detail"""
        try:
            info_msg(f"Analyzing engagement @{username}...")
            
            user_info = self.client.user_info_by_username(username)
            user_id = user_info.pk
            
            # Get posts
            medias = self.client.user_medias(user_id, amount=50)
            
            if not medias:
                error_msg("Tidak ada posts")
                return None
            
            # Calculate metrics
            total_likes = sum(m.like_count for m in medias)
            total_comments = sum(m.comment_count for m in medias)
            avg_likes = total_likes / len(medias)
            avg_comments = total_comments / len(medias)
            
            # Find top posts
            top_3_posts = sorted(medias, key=lambda m: m.like_count + m.comment_count, reverse=True)[:3]
            
            # Engagement rate
            total_engagement = total_likes + total_comments
            engagement_rate = (total_engagement / (len(medias) * max(user_info.follower_count, 1))) * 100
            
            # Trend (bandingkan first 25 posts vs last 25 posts)
            first_half = medias[:25]
            second_half = medias[25:50]
            
            avg_engagement_first = sum(m.like_count + m.comment_count for m in first_half) / len(first_half) if first_half else 0
            avg_engagement_second = sum(m.like_count + m.comment_count for m in second_half) / len(second_half) if second_half else 0
            
            trend = "📈 UP" if avg_engagement_second > avg_engagement_first else "📉 DOWN"
            trend_pct = ((avg_engagement_second - avg_engagement_first) / max(avg_engagement_first, 1)) * 100
            
            analytics = {
                'username': username,
                'followers': user_info.follower_count,
                'posts_analyzed': len(medias),
                'total_likes': total_likes,
                'total_comments': total_comments,
                'avg_likes': avg_likes,
                'avg_comments': avg_comments,
                'engagement_rate': engagement_rate,
                'total_engagement': total_engagement,
                'trend': trend,
                'trend_pct': trend_pct,
                'top_posts': [
                    {
                        'likes': p.like_count,
                        'comments': p.comment_count,
                        'caption': p.caption_text[:50] if p.caption_text else 'No caption',
                        'date': p.taken_at.isoformat() if p.taken_at else None
                    }
                    for p in top_3_posts
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            return analytics
            
        except Exception as e:
            error_msg(f"Error analyze engagement: {str(e)}")
            return None

    def display_analytics(self, analytics):
        """Display analytics dengan formatting"""
        if not analytics:
            return
        
        show_separator()
        print(Fore.CYAN + f"\n📊 ENGAGEMENT ANALYTICS - @{analytics['username']}" + Style.RESET_ALL)
        show_separator()
        
        print(Fore.YELLOW + "\n📈 MAIN METRICS:" + Style.RESET_ALL)
        print(f"  👥 Followers: {analytics['followers']:,}")
        print(f"  📸 Posts Analyzed: {analytics['posts_analyzed']}")
        print(f"  ❤️  Total Likes: {analytics['total_likes']:,}")
        print(f"  💬 Total Comments: {analytics['total_comments']:,}")
        
        print(Fore.YELLOW + "\n📊 AVERAGES:" + Style.RESET_ALL)
        print(f"  ❤️  Avg Likes/Post: {analytics['avg_likes']:.1f}")
        print(f"  💬 Avg Comments/Post: {analytics['avg_comments']:.1f}")
        print(f"  📊 Engagement Rate: {analytics['engagement_rate']:.2f}%")
        print(f"  📈 Total Engagement: {analytics['total_engagement']:,}")
        
        print(Fore.YELLOW + f"\n🔄 TREND: {analytics['trend']} {analytics['trend_pct']:+.1f}%" + Style.RESET_ALL)
        
        print(Fore.YELLOW + "\n🏆 TOP 3 POSTS:" + Style.RESET_ALL)
        for i, post in enumerate(analytics['top_posts'], 1):
            total = post['likes'] + post['comments']
            print(f"  {i}. ❤️ {post['likes']:,} | 💬 {post['comments']:,} | Total: {total:,}")
            print(f"     Caption: {post['caption']}")

    def export_analytics(self, analytics, format_type="json"):
        """Export analytics ke file"""
        try:
            if format_type == "json":
                filename = f"analytics/engagement_{analytics['username']}_{int(datetime.now().timestamp())}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(analytics, f, indent=4, ensure_ascii=False)
            
            elif format_type == "csv":
                filename = f"analytics/engagement_{analytics['username']}_{int(datetime.now().timestamp())}.csv"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Metric,Value\n")
                    f.write(f"Username,{analytics['username']}\n")
                    f.write(f"Followers,{analytics['followers']}\n")
                    f.write(f"Avg Likes,{analytics['avg_likes']:.1f}\n")
                    f.write(f"Avg Comments,{analytics['avg_comments']:.1f}\n")
                    f.write(f"Engagement Rate,{analytics['engagement_rate']:.2f}%\n")
                    f.write(f"Trend,{analytics['trend']} {analytics['trend_pct']:+.1f}%\n")
            
            success_msg(f"✅ Exported to {filename}")
            return filename
            
        except Exception as e:
            error_msg(f"Error export: {str(e)}")
            return None

    def run_analytics_menu(self, username):
        """Menu engagement analytics"""
        show_separator()
        print(Fore.CYAN + "\n📊 ENGAGEMENT ANALYTICS - ENHANCED" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nPilih aksi:" + Style.RESET_ALL)
            print("1. 📊 Analyze current account")
            print("2. 📋 Analyze multiple accounts")
            print("3. 📈 Compare trend over time")
            print("0. ❌ Batal")
            
            choice = input(Fore.MAGENTA + "\nPilih (0-3): " + Style.RESET_ALL).strip()
            
            if choice == '0':
                info_msg("Dibatalkan")
                return
            
            elif choice == '1':
                analytics = self.analyze_engagement(username)
                if analytics:
                    self.display_analytics(analytics)
                    
                    export_choice = input(Fore.MAGENTA + "\nExport hasil? (yes/no): " + Style.RESET_ALL).strip().lower()
                    if export_choice == "yes":
                        self.export_analytics(analytics)
            
            elif choice == '2':
                usernames_input = input(Fore.YELLOW + "\nMasukkan username(s) (pisahkan koma): " + Style.RESET_ALL).strip()
                usernames = [u.strip() for u in usernames_input.split(',')]
                
                all_analytics = []
                for uname in usernames:
                    analytics = self.analyze_engagement(uname)
                    if analytics:
                        all_analytics.append(analytics)
                        self.display_analytics(analytics)
                
                if all_analytics:
                    export_choice = input(Fore.MAGENTA + "\nExport hasil? (yes/no): " + Style.RESET_ALL).strip().lower()
                    if export_choice == "yes":
                        for analytics in all_analytics:
                            self.export_analytics(analytics)
            
            elif choice == '3':
                warning_msg("Feature trend comparison coming soon!")

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def engagement_analytics_menu(client, username):
    """Menu wrapper"""
    analytics = EngagementAnalyticsEnhanced(client)
    analytics.run_analytics_menu(username)
