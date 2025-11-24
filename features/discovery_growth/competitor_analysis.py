#!/usr/bin/env python3
"""
Competitor Analysis
Compare performa akun dengan kompetitor
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import json
import os
import time

class CompetitorAnalysis:
    def __init__(self, client):
        self.client = client

    def analyze_account(self, username):
        """Analyze single account"""
        try:
            info_msg(f"Analyzing @{username}...")
            
            user_info = self.client.user_info_by_username(username)
            user_id = user_info.pk
            
            # Get recent posts
            medias = self.client.user_medias(user_id, amount=20)
            
            total_likes = sum(m.like_count for m in medias)
            total_comments = sum(m.comment_count for m in medias)
            avg_likes = total_likes / len(medias) if medias else 0
            avg_comments = total_comments / len(medias) if medias else 0
            
            # Find top post
            top_post = max(medias, key=lambda m: m.like_count) if medias else None
            
            analysis = {
                'username': username,
                'followers': user_info.follower_count,
                'following': user_info.following_count,
                'posts': user_info.media_count,
                'avg_likes': avg_likes,
                'avg_comments': avg_comments,
                'total_engagement': total_likes + total_comments,
                'engagement_rate': ((total_likes + total_comments) / (len(medias) * max(user_info.follower_count, 1))) * 100 if medias else 0,
                'bio': user_info.biography,
                'top_post_likes': top_post.like_count if top_post else 0,
                'top_post_comments': top_post.comment_count if top_post else 0,
                'is_verified': user_info.is_verified,
                'is_private': user_info.is_private
            }
            
            return analysis
            
        except Exception as e:
            error_msg(f"Error analyze @{username}: {str(e)}")
            return None

    def compare_accounts(self, own_analysis, competitor_analyses):
        """Compare own account dengan competitors"""
        try:
            comparison = {
                'own': own_analysis,
                'competitors': competitor_analyses,
                'comparison_metrics': {}
            }
            
            # Hitung ranking untuk setiap metric
            for metric in ['followers', 'avg_likes', 'avg_comments', 'engagement_rate', 'posts']:
                all_values = [own_analysis[metric]] + [c[metric] for c in competitor_analyses]
                own_rank = sorted(all_values, reverse=True).index(own_analysis[metric]) + 1
                comparison['comparison_metrics'][metric] = {
                    'own_value': own_analysis[metric],
                    'rank': own_rank,
                    'total_competitors': len(competitor_analyses)
                }
            
            return comparison
            
        except Exception as e:
            error_msg(f"Error compare: {str(e)}")
            return None

    def display_analysis(self, analysis, title="ANALYSIS"):
        """Display account analysis"""
        if not analysis:
            return
        
        print(Fore.YELLOW + f"\n📊 {title} - @{analysis['username']}" + Style.RESET_ALL)
        print(f"  👥 Followers: {analysis['followers']:,}")
        print(f"  🔗 Following: {analysis['following']:,}")
        print(f"  📸 Posts: {analysis['posts']}")
        print(f"  ❤️  Avg Likes: {analysis['avg_likes']:.0f}")
        print(f"  💬 Avg Comments: {analysis['avg_comments']:.1f}")
        print(f"  📈 Engagement Rate: {analysis['engagement_rate']:.2f}%")
        print(f"  ✅ Verified: {'Yes' if analysis['is_verified'] else 'No'}")

    def display_comparison(self, comparison):
        """Display comparison results"""
        if not comparison:
            return
        
        show_separator()
        print(Fore.CYAN + "\n📊 COMPETITOR ANALYSIS COMPARISON" + Style.RESET_ALL)
        show_separator()
        
        self.display_analysis(comparison['own'], "YOUR ACCOUNT")
        
        for comp in comparison['competitors']:
            self.display_analysis(comp, "COMPETITOR")
        
        # Ranking
        print(Fore.YELLOW + "\n🏆 RANKING ANALYSIS:" + Style.RESET_ALL)
        
        for metric, data in comparison['comparison_metrics'].items():
            rank = data['rank']
            total = data['total_competitors'] + 1
            status = "🥇 1st" if rank == 1 else f"#{rank} of {total}"
            print(f"  {metric.upper()}: {status}")

    def run_competitor_analysis(self, own_username):
        """Menu competitor analysis"""
        show_separator()
        print(Fore.CYAN + "\n📊 COMPETITOR ANALYSIS" + Style.RESET_ALL)
        show_separator()

        try:
            # Analyze own account
            print(Fore.YELLOW + "\nAnalyzing your account..." + Style.RESET_ALL)
            own_analysis = self.analyze_account(own_username)
            
            if not own_analysis:
                return
            
            # Input competitor usernames
            print(Fore.YELLOW + "\nInput kompetitor username(s) (2-5):" + Style.RESET_ALL)
            print("  Contoh: competitor1, competitor2, competitor3")
            
            competitor_input = input(Fore.YELLOW + "\nKompetitors: " + Style.RESET_ALL).strip()
            
            if not competitor_input:
                error_msg("Competitor tidak boleh kosong!")
                return
            
            competitors = [c.strip() for c in competitor_input.split(',')]
            competitors = [c for c in competitors if c]
            
            if len(competitors) < 2:
                error_msg("Minimal 2 kompetitor!")
                return
            
            if len(competitors) > 5:
                warning_msg("Maksimal 5 kompetitor, menggunakan 5 yang pertama")
                competitors = competitors[:5]
            
            # Analyze competitors
            competitor_analyses = []
            for i, competitor in enumerate(competitors, 1):
                try:
                    print(Fore.YELLOW + f"\n[{i}/{len(competitors)}] Analyzing @{competitor}..." + Style.RESET_ALL)
                    comp_analysis = self.analyze_account(competitor)
                    if comp_analysis:
                        competitor_analyses.append(comp_analysis)
                    time.sleep(2)  # Delay antar analysis
                except:
                    continue
            
            if not competitor_analyses:
                error_msg("Tidak ada competitor yang berhasil di-analyze")
                return
            
            # Compare
            comparison = self.compare_accounts(own_analysis, competitor_analyses)
            
            if comparison:
                self.display_comparison(comparison)
                
                # Export
                save_choice = input(Fore.MAGENTA + "\nSimpan report? (yes/no): " + Style.RESET_ALL).strip().lower()
                
                if save_choice == "yes":
                    export_file = f"data/competitor_analysis_{int(time.time())}.json"
                    os.makedirs("data", exist_ok=True)
                    
                    with open(export_file, 'w', encoding='utf-8') as f:
                        json.dump(comparison, f, indent=4, ensure_ascii=False)
                    
                    success_msg(f"✅ Report saved to {export_file}")

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def competitor_analysis_menu(client, username):
    """Menu wrapper"""
    analysis = CompetitorAnalysis(client)
    analysis.run_competitor_analysis(username)
