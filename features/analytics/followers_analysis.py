#!/usr/bin/env python3
"""
Analisis Followers (follower baru, unfollowers, tidak follow back, ghost followers)
"""

from colorama import Fore, Style
from banner import success_msg, error_msg, info_msg, show_separator

def followers_menu(client, username):
    show_separator()
    print(Fore.YELLOW + "\n👥 ANALISIS FOLLOWERS" + Style.RESET_ALL)
    show_separator()
    print(Fore.GREEN + "1. List followers terbaru")
    print(Fore.GREEN + "2. List unfollowers (unfollow lu)")
    print(Fore.GREEN + "3. Followers tidak follow back")
    print(Fore.GREEN + "4. Ghost followers (tidak engage)")
    print(Fore.RED + "0. Kembali" + Style.RESET_ALL)
    show_separator()

    choice = input(Fore.MAGENTA + "\nPilih menu followers (0-4): " + Style.RESET_ALL).strip()

    if choice == "1":
        list_latest_followers(client, username)
    elif choice == "2":
        list_unfollowers(client, username)
    elif choice == "3":
        list_not_followback(client, username)
    elif choice == "4":
        list_ghost_followers(client, username)
    elif choice == "0":
        return
    else:
        error_msg("Pilihan tidak valid!")
        input("Tekan Enter untuk kembali...")

def list_latest_followers(client, username):
    show_separator()
    print(Fore.CYAN + "\nFollowers Terbaru (10 paling baru):" + Style.RESET_ALL)
    followers = client.user_followers(client.user_id, amount=10)
    for f in followers.values():
        print(Fore.GREEN + f"- @{f.username} | {f.full_name}")
    input(Fore.MAGENTA + "\nTekan Enter untuk kembali...")

def list_unfollowers(client, username):
    show_separator()
    print(Fore.CYAN + "\nUnfollowers (unfollow lu):" + Style.RESET_ALL)
    followers_set = set(client.user_followers(client.user_id))
    following_set = set(client.user_following(client.user_id))
    unfollowers = following_set - followers_set
    for uid in list(unfollowers)[:10]:
        user = client.user_info(uid)
        print(Fore.RED + f"- @{user.username} | {user.full_name}")
    input(Fore.MAGENTA + "\nTekan Enter untuk kembali...")

def list_not_followback(client, username):
    show_separator()
    print(Fore.CYAN + "\nFollowers yang tidak you follow back:\n" + Style.RESET_ALL)
    followers = set(client.user_followers(client.user_id))
    following = set(client.user_following(client.user_id))
    not_followed_back = followers - following
    for uid in list(not_followed_back)[:10]:
        user = client.user_info(uid)
        print(Fore.YELLOW + f"- @{user.username} | {user.full_name}")
    input(Fore.MAGENTA + "\nTekan Enter untuk kembali...")

def list_ghost_followers(client, username):
    show_separator()
    print(Fore.CYAN + "\nGhost Followers (followers yang nggak pernah like atau komen):" + Style.RESET_ALL)
    # Sederhana: followers yang nggak pernah like/komen 10 posting terakhir
    followers = client.user_followers(client.user_id)
    user_ids = set(followers.keys())
    medias = client.user_medias_v1(client.user_id, amount=10)
    engaged = set()
    for m in medias:
        likers = set(client.media_likers(m.id))
        commenters = set([c.user_id for c in client.media_comments(m.id)])
        engaged.update(likers)
        engaged.update(commenters)
    ghost = user_ids - engaged
    for uid in list(ghost)[:10]:
        user = followers[uid]
        print(Fore.LIGHTBLACK_EX + f"- @{user.username}")
    input(Fore.MAGENTA + "\nTekan Enter untuk kembali...")

