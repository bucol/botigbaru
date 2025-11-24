#!/usr/bin/env python3
"""
Banner untuk Bucol Bot Instagram
"""

from colorama import Fore, Style, init

def show_banner():
    """Tampilkan banner Bucol Bot Instagram - Garis Lurus & Simetris"""
    init(autoreset=True)
    
    banner_art = f"""{Fore.CYAN}╔═════════════════════════════════════════════════════════════╗
║  {Fore.MAGENTA}██████╗ {Fore.YELLOW}██╗   ██╗ {Fore.GREEN}██████╗ {Fore.RED} ██████╗ {Fore.BLUE}██╗{Fore.CYAN}          ║
║  {Fore.MAGENTA}██╔══██╗{Fore.YELLOW}██║   ██║{Fore.GREEN}██╔════╝ {Fore.RED}██╔═══██╗{Fore.BLUE}██║{Fore.CYAN}          ║
║  {Fore.MAGENTA}██████╔╝{Fore.YELLOW}██║   ██║{Fore.GREEN}██║      {Fore.RED}██║   ██║{Fore.BLUE}██║{Fore.CYAN}          ║
║  {Fore.MAGENTA}██╔══██╗{Fore.YELLOW}██║   ██║{Fore.GREEN}██║      {Fore.RED}██║   ██║{Fore.BLUE}██║{Fore.CYAN}          ║
║  {Fore.MAGENTA}██████╔╝{Fore.YELLOW}╚██████╔╝{Fore.GREEN}╚██████╗ {Fore.RED}╚██████╔╝{Fore.BLUE}███████╗{Fore.CYAN}      ║
║  {Fore.MAGENTA}╚═════╝ {Fore.YELLOW} ╚═════╝ {Fore.GREEN} ╚═════╝ {Fore.RED} ╚═════╝ {Fore.BLUE}╚══════╝{Fore.CYAN}      ║
╠═════════════════════════════════════════════════════════════╣
║        {Fore.YELLOW}🤖 BUCOL BOT INSTAGRAM - v2.0 🤖{Fore.CYAN}               ║
║        {Fore.GREEN}📱 Instagram Account Manager 📱{Fore.CYAN}                ║
║        {Fore.MAGENTA}✨ Untuk Edukasi Pribadi ✨{Fore.CYAN}                   ║
╚═════════════════════════════════════════════════════════════╝{Style.RESET_ALL}"""
    
    print(banner_art)

def show_separator():
    """Tampilkan separator"""
    print(f"{Fore.CYAN}═════════════════════════════════════════════════════════════{Style.RESET_ALL}")

def success_msg(text):
    """Pesan sukses"""
    print(f"{Fore.GREEN}✅ {text}{Style.RESET_ALL}")

def error_msg(text):
    """Pesan error"""
    print(f"{Fore.RED}❌ {text}{Style.RESET_ALL}")

def info_msg(text):
    """Pesan info"""
    print(f"{Fore.CYAN}ℹ️  {text}{Style.RESET_ALL}")

def warning_msg(text):
    """Pesan warning"""
    print(f"{Fore.YELLOW}⚠️  {text}{Style.RESET_ALL}")
