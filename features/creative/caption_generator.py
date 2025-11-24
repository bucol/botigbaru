#!/usr/bin/env python3
"""
Caption Generator
Generate caption otomatis dengan tema, mood, dan hashtag
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import random
import json
import os

class CaptionGenerator:
    def __init__(self):
        self.templates_dir = "data/caption_templates"
        self.load_templates()

    def load_templates(self):
        """Load caption templates dari file"""
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Default templates
        self.templates = {
            'inspirational': [
                "Every moment is a fresh beginning. Take it! ✨",
                "The only way to do great work is to love what you do. 💪",
                "Be yourself; everyone else is already taken. 🌟",
                "Success is not final, failure is not fatal. Keep going! 🚀",
                "Your limitation—it's only your imagination. 🎯",
                "Dream big and dare to fail. 💫",
                "The future is bright, and it starts today. ☀️",
                "Believe in yourself and you're halfway there. 🔥"
            ],
            'funny': [
                "Me: *tries to act cool* Also me: *trips over air* 😂",
                "POV: You're about to see a really bad decision 🎬",
                "Mood: Chaotic energy ✨ (jk I'm fine) 🤡",
                "The audacity of me posting this 💀",
                "This is what it means to be alive in 2025 😵",
                "Plot twist: I actually know what I'm doing 🤪",
                "Living my best unplanned life rn 🌪️",
                "Confidence level: posting this without overthinking 🙃"
            ],
            'promotional': [
                "Check out what's new! 🎉 Link in bio 👆",
                "Available now! Don't miss out 🔥 #limited",
                "Something special is coming your way ✨",
                "Tag someone who needs this 👇",
                "This is too good to miss! 📸",
                "Swipe to see more ➡️ #exclusive",
                "Your next favorite thing 💕 #newdrop",
                "DM for details! 📩"
            ],
            'casual': [
                "Just vibing 🌊",
                "Living that life 📸",
                "Feeling myself today 😎",
                "Proof I actually went outside 🌞",
                "Caught in the moment ✨",
                "That's how we do it 💁‍♀️",
                "Simple things = best things 💫",
                "Current mood: grateful 🙏"
            ],
            'professional': [
                "Excited to announce... 📢",
                "Focused on what matters. 🎯",
                "Collaboration makes it better. 🤝",
                "Building something amazing. 🚀",
                "Grateful for this journey. 📈",
                "Passion meets purpose. ⚡",
                "Every day is an opportunity. 💼",
                "Excellence is the standard. ✅"
            ]
        }

    def generate_captions(self, mood, theme="", num_variants=5):
        """Generate caption variants"""
        try:
            if mood not in self.templates:
                error_msg(f"Mood '{mood}' tidak ada. Pilih dari: {', '.join(self.templates.keys())}")
                return None

            template_list = self.templates[mood]
            captions = []

            for _ in range(num_variants):
                # Pilih base caption
                base = random.choice(template_list)
                
                # Add theme jika ada
                if theme:
                    base += f"\n\n#{theme}"

                # Add random hashtags
                hashtags = self.generate_hashtags(theme if theme else mood)
                base += f"\n{hashtags}"

                captions.append(base)

            return captions

        except Exception as e:
            error_msg(f"Error generate: {str(e)}")
            return None

    def generate_hashtags(self, keyword, count=10):
        """Generate relevant hashtags"""
        try:
            # Default hashtag templates
            hashtag_templates = {
                'fashion': ['fashion', 'ootd', 'style', 'fashionista', 'streetstyle', 'lookbook', 'fashionblogger', 'outfitoftheday', 'fashiongram', 'styleblogger'],
                'photography': ['photography', 'photographer', 'photooftheday', 'picoftheday', 'instapic', 'photoart', 'instaphoto', 'camerart', 'photolife', 'shutterstock'],
                'lifestyle': ['lifestyle', 'lifestyleblogger', 'dailylife', 'lifestylegoals', 'instalife', 'lifeinspo', 'motivation', 'goals', 'inspo', 'vibes'],
                'food': ['foodie', 'foodporn', 'instafood', 'foodphotography', 'foodblogger', 'delicious', 'foodgasm', 'eeeeeats', 'foodstagram', 'yummy'],
                'travel': ['travel', 'travelgram', 'wanderlust', 'travelphotography', 'instatravel', 'traveling', 'traveladdict', 'adventuretime', 'explorepage', 'vacation'],
                'fitness': ['fitness', 'gym', 'workout', 'fitnessmotivation', 'bodybuilding', 'fitnessmodel', 'healthylifestyle', 'fitfam', 'gains', 'fitnessgirl']
            }

            # Match keyword ke category
            matched_hashtags = []
            for category, tags in hashtag_templates.items():
                if keyword.lower() in category or category in keyword.lower():
                    matched_hashtags = tags
                    break

            # Jika tidak match, generate generic
            if not matched_hashtags:
                matched_hashtags = ['instagood', 'insta', 'instagram', 'photooftheday', 'picoftheday', 'like', 'follow', 'comment', 'share', 'love']

            # Random select
            selected = random.sample(matched_hashtags, min(count, len(matched_hashtags)))
            hashtag_string = " ".join([f"#{tag}" for tag in selected])

            return hashtag_string

        except Exception as e:
            error_msg(f"Error generate hashtags: {str(e)}")
            return "#instagood #insta #instagram"

    def display_captions(self, captions):
        """Display generated captions"""
        if not captions:
            return

        print(Fore.CYAN + "\n✨ GENERATED CAPTIONS" + Fore.RESET + "\n")

        for i, caption in enumerate(captions, 1):
            print(Fore.YELLOW + f"━━━ OPTION {i} ━━━" + Style.RESET_ALL)
            print(caption)
            print()

    def run_generator_menu(self):
        """Menu caption generator"""
        show_separator()
        print(Fore.CYAN + "\n✍️  CAPTION GENERATOR" + Style.RESET_ALL)
        show_separator()

        try:
            print(Fore.YELLOW + "\nPilih mood:" + Style.RESET_ALL)
            moods = list(self.templates.keys())
            for i, mood in enumerate(moods, 1):
                print(f"{i}. {mood.upper()}")

            mood_choice = input(Fore.MAGENTA + "\nPilih (1-{0}): ".format(len(moods)) + Style.RESET_ALL).strip()

            try:
                mood_idx = int(mood_choice) - 1
                if 0 <= mood_idx < len(moods):
                    mood = moods[mood_idx]
                else:
                    error_msg("Pilihan tidak valid!")
                    return
            except ValueError:
                error_msg("Input harus angka!")
                return

            theme = input(Fore.YELLOW + "\nTheme/Keyword (opsional): " + Style.RESET_ALL).strip()

            num_variants = input(Fore.YELLOW + "Jumlah variants (default: 5): " + Style.RESET_ALL).strip()
            num_variants = int(num_variants) if num_variants else 5

            info_msg("Generating captions...")
            captions = self.generate_captions(mood, theme, num_variants)

            if captions:
                self.display_captions(captions)

                # Save to clipboard / file
                save_choice = input(Fore.MAGENTA + "\nSimpan ke file? (yes/no): " + Style.RESET_ALL).strip().lower()

                if save_choice == "yes":
                    filename = f"data/captions_{mood}_{int(__import__('time').time())}.txt"
                    os.makedirs("data", exist_ok=True)
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        for i, caption in enumerate(captions, 1):
                            f.write(f"--- OPTION {i} ---\n")
                            f.write(caption)
                            f.write("\n\n")

                    success_msg(f"✅ Saved to {filename}")

                # Copy first caption
                copy_choice = input(Fore.MAGENTA + "\nCopy caption ke clipboard? (yes/no): " + Style.RESET_ALL).strip().lower()

                if copy_choice == "yes":
                    try:
                        import pyperclip
                        pyperclip.copy(captions[0])
                        success_msg("✅ Copied to clipboard!")
                    except:
                        info_msg("Install pyperclip untuk fitur copy: pip install pyperclip")

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def caption_generator_menu():
    """Menu wrapper"""
    generator = CaptionGenerator()
    generator.run_generator_menu()
