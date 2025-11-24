#!/usr/bin/env python3
"""
Hashtag Research Tool
Cari dan research hashtag populer untuk niche tertentu
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import json
import os
import time

class HashtagResearch:
    def __init__(self, client):
        self.client = client
        self.hashtag_cache_file = "data/hashtag_cache.json"
        self.load_cache()

    def load_cache(self):
        """Load hashtag cache dari file"""
        if os.path.exists(self.hashtag_cache_file):
            try:
                with open(self.hashtag_cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
        else:
            os.makedirs("data", exist_ok=True)
            self.cache = {}

    def save_cache(self):
        """Simpan hashtag cache ke file"""
        try:
            with open(self.hashtag_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=4, ensure_ascii=False)
        except Exception as e:
            warning_msg(f"Error save cache: {str(e)}")

    def research_hashtag(self, hashtag):
        """Research single hashtag stats"""
        try:
            info_msg(f"Researching #{hashtag}...")
            
            # Check cache
            if hashtag in self.cache:
                info_msg(f"Loading from cache (cached)")
                return self.cache[hashtag]
            
            # Get hashtag info
            hashtag_info = self.client.hashtag_info_by_name(hashtag)
            
            stats = {
                'name': hashtag,
                'posts': hashtag_info.media_count,
                'searched': True,
                'timestamp': time.time()
            }
            
            # Classify size
            if stats['posts'] < 10000:
                stats['size'] = 'MICRO (< 10K)'
                stats['difficulty'] = 'EASY'
            elif stats['posts'] < 100000:
                stats['size'] = 'SMALL (10K-100K)'
                stats['difficulty'] = 'EASY-MEDIUM'
            elif stats['posts'] < 1000000:
                stats['size'] = 'MEDIUM (100K-1M)'
                stats['difficulty'] = 'MEDIUM'
            elif stats['posts'] < 10000000:
                stats['size'] = 'LARGE (1M-10M)'
                stats['difficulty'] = 'HARD'
            else:
                stats['size'] = 'MEGA (> 10M)'
                stats['difficulty'] = 'VERY HARD'
            
            self.cache[hashtag] = stats
            self.save_cache()
            
            return stats
            
        except Exception as e:
            error_msg(f"Error research hashtag: {str(e)}")
            return None

    def get_hashtag_strategy(self, niche_hashtags, ratio_type="balanced"):
        """
        Generate hashtag strategy berdasarkan ratio
        ratio_type: balanced (30% high, 40% medium, 30% low)
                    aggressive (20% high, 30% medium, 50% low)
                    conservative (50% high, 30% medium, 20% low)
        """
        try:
            researched = []
            
            info_msg(f"Researching {len(niche_hashtags)} hashtags...")
            
            for hashtag in niche_hashtags:
                stats = self.research_hashtag(hashtag)
                if stats:
                    researched.append(stats)
                time.sleep(1)  # Delay per hashtag
            
            if not researched:
                error_msg("Tidak ada hashtag yang berhasil di-research")
                return None
            
            # Classify by difficulty
            easy = [h for h in researched if h['difficulty'] in ['EASY', 'EASY-MEDIUM']]
            medium = [h for h in researched if h['difficulty'] == 'MEDIUM']
            hard = [h for h in researched if h['difficulty'] in ['HARD', 'VERY HARD']]
            
            # Apply ratio
            if ratio_type == "balanced":
                ratio = {'high': 0.30, 'medium': 0.40, 'low': 0.30}  # high=hard, medium=medium, low=easy
            elif ratio_type == "aggressive":
                ratio = {'high': 0.20, 'medium': 0.30, 'low': 0.50}
            else:  # conservative
                ratio = {'high': 0.50, 'medium': 0.30, 'low': 0.20}
            
            # Calculate counts
            total = len(researched)
            high_count = max(1, int(total * ratio['high']))
            medium_count = max(1, int(total * ratio['medium']))
            low_count = total - high_count - medium_count
            
            # Select hashtags
            strategy = {
                'high_difficulty': hard[:high_count] if hard else easy[:high_count],
                'medium_difficulty': medium[:medium_count],
                'low_difficulty': easy[:low_count]
            }
            
            return strategy
            
        except Exception as e:
            error_msg(f"Error generate strategy: {str(e)}")
            return None

    def display_hashtag_stats(self, stats):
        """Display hashtag stats dengan formatting"""
        if not stats:
            return
        
        print(Fore.YELLOW + f"\n  #{stats['name']}" + Style.RESET_ALL)
        print(f"    Posts: {stats['posts']:,}")
        print(f"    Size: {stats['size']}")
        print(f"    Difficulty: {stats['difficulty']}")

    def run_research_menu(self):
        """Menu hashtag research"""
        show_separator()
        print(Fore.CYAN + "\n🏷️  HASHTAG RESEARCH TOOL" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nInput niche/keywords (pisahkan dengan koma):" + Style.RESET_ALL)
            print("  Contoh: fashion, photography, lifestyle")
            
            keywords_input = input(Fore.YELLOW + "\nKeywords: " + Style.RESET_ALL).strip()
            
            if not keywords_input:
                error_msg("Keywords tidak boleh kosong!")
                return
            
            keywords = [k.strip() for k in keywords_input.split(',')]
            keywords = [k for k in keywords if k]
            
            # Generate hashtags dari keywords (sample hashtags)
            niche_hashtags = []
            for keyword in keywords:
                # Generate common hashtags for keyword
                base_hashtags = [
                    keyword,
                    f"{keyword}photography",
                    f"{keyword}tips",
                    f"{keyword}inspiration",
                    f"{keyword}love",
                    f"{keyword}community"
                ]
                niche_hashtags.extend(base_hashtags[:3])  # Take 3 per keyword
            
            niche_hashtags = list(set(niche_hashtags))  # Remove duplicates
            
            print(Fore.YELLOW + f"\n📊 Researching {len(niche_hashtags)} hashtags..." + Style.RESET_ALL)
            
            # Research hashtags
            research_results = []
            for i, hashtag in enumerate(niche_hashtags, 1):
                try:
                    stats = self.research_hashtag(hashtag)
                    if stats:
                        research_results.append(stats)
                        self.display_hashtag_stats(stats)
                    print(f"  [{i}/{len(niche_hashtags)}]")
                except:
                    continue
            
            if not research_results:
                error_msg("Tidak ada hashtag yang berhasil di-research")
                return
            
            # Show strategy
            print(Fore.YELLOW + "\n⚖️  Pilih strategi hashtag:" + Style.RESET_ALL)
            print("1. 🎯 Balanced (30% high, 40% medium, 30% low)")
            print("2. 🚀 Aggressive (20% high, 30% medium, 50% low)")
            print("3. 🛡️  Conservative (50% high, 30% medium, 20% low)")
            
            strategy_choice = input(Fore.MAGENTA + "\nPilih (1-3): " + Style.RESET_ALL).strip()
            
            strategy_map = {
                '1': 'balanced',
                '2': 'aggressive',
                '3': 'conservative'
            }
            
            strategy_type = strategy_map.get(strategy_choice, 'balanced')
            
            # Generate strategy
            strategy = self.get_hashtag_strategy(niche_hashtags, strategy_type)
            
            if strategy:
                print(Fore.GREEN + "\n✅ HASHTAG STRATEGY GENERATED" + Style.RESET_ALL)
                print(Fore.YELLOW + f"\nStrategy Type: {strategy_type.upper()}" + Style.RESET_ALL)
                
                print(Fore.YELLOW + f"\n🔴 HIGH DIFFICULTY ({len(strategy['high_difficulty'])}):" + Style.RESET_ALL)
                for h in strategy['high_difficulty']:
                    self.display_hashtag_stats(h)
                
                print(Fore.YELLOW + f"\n🟡 MEDIUM DIFFICULTY ({len(strategy['medium_difficulty'])}):" + Style.RESET_ALL)
                for h in strategy['medium_difficulty']:
                    self.display_hashtag_stats(h)
                
                print(Fore.YELLOW + f"\n🟢 LOW DIFFICULTY ({len(strategy['low_difficulty'])}):" + Style.RESET_ALL)
                for h in strategy['low_difficulty']:
                    self.display_hashtag_stats(h)
                
                # Export
                save_choice = input(Fore.MAGENTA + "\nSimpan ke file? (yes/no): " + Style.RESET_ALL).strip().lower()
                
                if save_choice == "yes":
                    export_file = f"data/hashtag_strategy_{int(time.time())}.json"
                    os.makedirs("data", exist_ok=True)
                    
                    with open(export_file, 'w', encoding='utf-8') as f:
                        json.dump(strategy, f, indent=4, ensure_ascii=False)
                    
                    success_msg(f"✅ Saved to {export_file}")

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def hashtag_research_menu(client):
    """Menu wrapper"""
    research = HashtagResearch(client)
    research.run_research_menu()
