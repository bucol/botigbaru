#!/usr/bin/env python3
"""
Story Template Maker
Buat template story dengan teks & elemen otomatis
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style
import json
import os
from datetime import datetime

class StoryTemplate:
    def __init__(self):
        self.templates_dir = "data/story_templates"
        os.makedirs(self.templates_dir, exist_ok=True)
        self.load_templates()

    def load_templates(self):
        """Load story templates"""
        self.templates = {
            'motivation': {
                'description': 'Motivational quote',
                'templates': [
                    'Today is a great day! 💪✨',
                    'Keep pushing forward! 🚀',
                    'You got this! 🔥',
                    'Never give up! 💫',
                    'Believe in yourself! 🌟'
                ]
            },
            'question': {
                'description': 'Ask followers question',
                'templates': [
                    'What\'s your favorite? 👇',
                    'Choose: A or B? 🤔',
                    'Hot take: Which one? ⬇️',
                    'Help me decide! 🆘',
                    'Quick poll! ⬇️'
                ]
            },
            'promotion': {
                'description': 'Promote content/product',
                'templates': [
                    'Check out the link in bio! 👆',
                    'Don\'t miss this! 🎉',
                    'Available now! 🔥',
                    'Limited time! ⏰',
                    'Swipe up! ➡️'
                ]
            },
            'daily': {
                'description': 'Daily life update',
                'templates': [
                    'Good morning! ☀️',
                    'Currently vibing... 🌊',
                    'Day in my life 📸',
                    'Just chillin\' 😎',
                    'Night time thoughts 🌙'
                ]
            },
            'selfie': {
                'description': 'Selfie template',
                'templates': [
                    'Feeling myself 💁',
                    'Mirror check ✨',
                    'Just because 📸',
                    'That glow tho 🌟',
                    'Confidence level ↗️'
                ]
            },
            'throwback': {
                'description': 'Throwback content',
                'templates': [
                    'Throwback to... 📷',
                    'Remember this? 🕰️',
                    'Good times 💭',
                    'Blast from the past 🎬',
                    'Old but gold ✨'
                ]
            }
        }

    def display_templates(self):
        """Display available templates"""
        show_separator()
        print(Fore.CYAN + "\n📸 STORY TEMPLATES" + Style.RESET_ALL)
        show_separator()

        for i, (key, data) in enumerate(self.templates.items(), 1):
            print(f"{i}. {key.upper()} - {data['description']}")

    def generate_story_text(self, template_key):
        """Generate story text dari template"""
        try:
            if template_key not in self.templates:
                error_msg("Template tidak ditemukan!")
                return None

            template_data = self.templates[template_key]
            base_text = random.choice(template_data['templates'])

            return base_text

        except Exception as e:
            error_msg(f"Error generate: {str(e)}")
            return None

    def customize_template(self, base_text):
        """Allow user customize template"""
        try:
            print(Fore.YELLOW + "\n📝 BASE TEXT:" + Style.RESET_ALL)
            print(base_text)

            custom = input(Fore.YELLOW + "\nCustomize text (tekan Enter skip): " + Style.RESET_ALL).strip()

            if custom:
                base_text = custom

            # Add emoji
            emoji_choice = input(Fore.YELLOW + "\nAdd emoji? (yes/no): " + Style.RESET_ALL).strip().lower()

            if emoji_choice == "yes":
                emoji_input = input(Fore.YELLOW + "Emoji: " + Style.RESET_ALL).strip()
                base_text += f" {emoji_input}"

            return base_text

        except Exception as e:
            error_msg(f"Error customize: {str(e)}")
            return base_text

    def save_template(self, template_name, text):
        """Save custom template"""
        try:
            filename = f"{self.templates_dir}/custom_{template_name}_{int(__import__('time').time())}.txt"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"Template: {template_name}\n")
                f.write(f"Created: {datetime.now().isoformat()}\n")
                f.write("---\n")
                f.write(text)

            success_msg(f"✅ Saved to {filename}")
            return filename

        except Exception as e:
            error_msg(f"Error save: {str(e)}")
            return None

    def run_template_menu(self):
        """Menu story template"""
        import random
        
        show_separator()
        print(Fore.CYAN + "\n📸 STORY TEMPLATE MAKER" + Style.RESET_ALL)
        show_separator()

        try:
            self.display_templates()

            choice = input(Fore.MAGENTA + "\nPilih template (nomor): " + Style.RESET_ALL).strip()

            try:
                template_idx = int(choice) - 1
                template_keys = list(self.templates.keys())

                if 0 <= template_idx < len(template_keys):
                    template_key = template_keys[template_idx]
                else:
                    error_msg("Pilihan tidak valid!")
                    return
            except ValueError:
                error_msg("Input harus angka!")
                return

            # Generate
            base_text = self.generate_story_text(template_key)

            if base_text:
                # Customize
                final_text = self.customize_template(base_text)

                show_separator()
                print(Fore.CYAN + "\n📋 FINAL STORY TEXT:" + Style.RESET_ALL)
                show_separator()
                print(Fore.YELLOW + final_text + Style.RESET_ALL)

                # Save
                save_choice = input(Fore.MAGENTA + "\nSave? (yes/no): " + Style.RESET_ALL).strip().lower()

                if save_choice == "yes":
                    self.save_template(template_key, final_text)

                # Copy
                try:
                    import pyperclip
                    copy_choice = input(Fore.MAGENTA + "\nCopy to clipboard? (yes/no): " + Style.RESET_ALL).strip().lower()

                    if copy_choice == "yes":
                        pyperclip.copy(final_text)
                        success_msg("✅ Copied!")
                except:
                    pass

        except Exception as e:
            error_msg(f"Error: {str(e)}")

def story_template_menu():
    """Menu wrapper"""
    template = StoryTemplate()
    template.run_template_menu()
