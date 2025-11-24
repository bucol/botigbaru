#!/usr/bin/env python3
"""
Modul: Post Reels Instagram
"""

from banner import success_msg, error_msg, info_msg, show_separator
from colorama import Fore, Style
import os

def post_reel(client):
    """Post reels Instagram"""
    show_separator()
    print(Fore.CYAN + "\n🎥 POST REELS INSTAGRAM" + Style.RESET_ALL)
    show_separator()
    
    video_path = input(Fore.YELLOW + "\nPath file video (mp4): " + Style.RESET_ALL).strip()
    video_path = video_path.strip('"').strip("'")
    
    if not os.path.exists(video_path):
        error_msg("File tidak ditemukan!")
        return
    
    caption = input(Fore.YELLOW + "Caption: " + Style.RESET_ALL).strip()
    
    try:
        info_msg("Posting reels...")
        media = client.clip_upload(video_path, caption)
        success_msg("Reels berhasil dipost! 🎉")
        print(Fore.GREEN + f"📱 Link: https://instagram.com/reel/{media.code}/" + Style.RESET_ALL)
        
    except Exception as e:
        error_msg(f"Error: {str(e)}")
