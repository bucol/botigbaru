#!/usr/bin/env python3
"""
Follower Growth Tracking:
Pantau pertambahan dan pengurangan followers harian dan mingguan
"""

import os
import json
from datetime import datetime, timedelta
from colorama import Fore, Style
from banner import show_separator, success_msg, error_msg, info_msg

DATA_FILE = "follower_growth.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def follower_growth(client, username):
    show_separator()
    print(Fore.CYAN + "\n📈 FOLLOWER GROWTH TRACKING" + Style.RESET_ALL)
    show_separator()
    
    try:
        current_followers = client.user_info_by_username(username).follower_count
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        
        data = load_data()
        
        # Simpan data hari ini jika belum ada
        if username not in data:
            data[username] = {}
            
        if today_str not in data[username]:
            data[username][today_str] = current_followers
            save_data(data)
            info_msg(f"Data followers hari ini ({today_str}) telah disimpan: {current_followers}")
        else:
            info_msg(f"Data followers hari ini ({today_str}) sudah tercatat: {data[username][today_str]}")
        
        # Hitung pertambahan/penurunan followers hari ini dibanding kemarin
        yesterday = now - timedelta(days=1)
        yesterday_str = yesterday.strftime("%Y-%m-%d")
        followers_yesterday = data[username].get(yesterday_str)
        
        if followers_yesterday is not None:
            diff = current_followers - followers_yesterday
            if diff > 0:
                print(Fore.GREEN + f"\n📅 Pertambahan followers sejak kemarin: +{diff}")
            elif diff < 0:
                print(Fore.RED + f"\n📅 Penurunan followers sejak kemarin: {diff}")
            else:
                print(Fore.YELLOW + "\n📅 Followers tidak berubah sejak kemarin.")
        else:
            info_msg("Data followers kemarin tidak tersedia.")
        
        # Hitung pertambahan/penurunan followers mingguan (7 hari)
        week_ago = now - timedelta(days=7)
        week_ago_str = week_ago.strftime("%Y-%m-%d")
        followers_week_ago = data[username].get(week_ago_str)
        
        if followers_week_ago is not None:
            diff_week = current_followers - followers_week_ago
            if diff_week > 0:
                print(Fore.GREEN + f"\n📅 Pertambahan followers dalam 7 hari terakhir: +{diff_week}")
            elif diff_week < 0:
                print(Fore.RED + f"\n📅 Penurunan followers dalam 7 hari terakhir: {diff_week}")
            else:
                print(Fore.YELLOW + "\n📅 Followers tidak berubah dalam 7 hari terakhir.")
        else:
            info_msg("Data followers seminggu lalu tidak tersedia.")
        
        success_msg("\n📊 Laporan follower growth selesai.")
    except Exception as e:
        error_msg(f"Error saat tracking follower growth: {str(e)}")
    
    input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)
