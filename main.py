#!/usr/bin/env python3
"""
Bucol Bot IG - Main Entry Point v4.0

Struktur sederhana:
- Test import semua core modules
- Tampilkan banner
- Menu utama dengan opsi dasar
"""

import sys
from pathlib import Path
from typing import Optional

# Pastikan core modules bisa diimport
try:
    from core.device_identity_generator import DeviceIdentityGenerator
    from core.verification_handler import VerificationHandler
    from core.session_manager_v2 import SessionManagerV2
    from core.account_manager import AccountManager
    from core.login_manager import LoginManager
except ImportError as e:
    print("X Error importing core modules: " + str(e))
    print("
W Pastikan folder 'core/' ada dan berisi:")
    print("   - device_identity_generator.py")
    print("   - verification_handler.py")
    print("   - session_manager_v2.py")
    print("   - account_manager.py")
    print("   - login_manager.py")
    sys.exit(1)


def show_banner():
    """Display banner bot"""
    print("
" + "=" * 70)
    banner = (
        "    BUCOL BOT INSTAGRAM v4.0 PRODUCTION
"
        "    Device Identity Anti-Detection System
"
        "    For Educational Purpose Only"
    )
    print(banner)
    print("=" * 70 + "
")


def test_modules():
    """Test semua core modules bisa jalan"""
    print("Checking core modules...
")

    try:
        # Device identity
        gen = DeviceIdentityGenerator()
        print("OK DeviceIdentityGenerator - " + str(len(gen.device_db)) + " devices loaded")

        # Verification handler
        verif = VerificationHandler()
        print("OK VerificationHandler - max_retries=" + str(verif.max_retries))

        # Session manager
        sess = SessionManagerV2()
        print("OK SessionManagerV2")

        # Account manager
        acc = AccountManager()
        print("OK AccountManager - " + str(len(acc.accounts_db)) + " accounts")

        # Login manager
        login = LoginManager()
        print("OK LoginManager")

        print("
" + "=" * 70)
        print("SUCCESS - All modules ready!")
        print("=" * 70 + "
")
        return True

    except Exception as e:
        print("
ERROR Module test failed: " + str(e))
        import traceback
        traceback.print_exc()
        return False


def menu_main():
    """Main menu loop"""
    while True:
        print("
MAIN MENU:")
        print("  1. Test Installation")
        print("  2. Quick Account Test (Register & Login Mock)")
        print("  3. List Accounts")
        print("  4. Statistics")
        print("  5. Run Test Suite")
        print("  0. Exit")

        choice = input("
Choose menu (0-5): ").strip()

        if choice == "1":
            test_modules()
        elif choice == "2":
            menu_account_test()
        elif choice == "3":
            menu_list_accounts()
        elif choice == "4":
            menu_statistics()
        elif choice == "5":
            menu_run_tests()
        elif choice == "0":
            print("
Bye!
")
            break
        else:
            print("Invalid choice!")


def menu_account_test():
    """Quick test: register & login (tanpa actual IG API)"""
    print("
" + "=" * 70)
    print("ACCOUNT REGISTRATION TEST")
    print("=" * 70 + "
")

    username = input("Input username (test_XXX): ").strip()
    if not username:
        print("ERROR Username cannot be empty")
        return

    password = input("Input password: ").strip()
    if not password:
        print("ERROR Password cannot be empty")
        return

    email = input("Input email (optional): ").strip() or None

    try:
        mgr = AccountManager()
        login_mgr = LoginManager()

        # Register
        print("
Registering...")
        ok, msg, data = mgr.register_account(
            username, login_mgr._hash_password(password), email=email
        )

        if ok:
            print("SUCCESS " + msg)
            device = data.get("device_identity", {})
            print("
   Device Model: " + device.get('model', 'N/A'))
            print("   Device ID: " + device.get('device_id', 'N/A')[:8] + "...")
            print("   Android Version: " + str(device.get('android_version', 'N/A')))

            # Mock login
            print("
Mock Login...")
            ok_login, msg_login, data_login = mgr.login_account(
                username, login_mgr._hash_password(password)
            )
            if ok_login:
                print("SUCCESS " + msg_login)
            else:
                print("ERROR " + msg_login)
        else:
            print("ERROR " + msg)

    except Exception as e:
        print("ERROR " + str(e))


def menu_list_accounts():
    """List all registered accounts"""
    print("
" + "=" * 70)
    print("REGISTERED ACCOUNTS")
    print("=" * 70 + "
")

    try:
        mgr = AccountManager()
        result = mgr.list_all_accounts()
        total = result.get("total", 0)
        accounts = result.get("accounts", [])

        if total == 0:
            print("No accounts registered yet.")
        else:
            print("Total: " + str(total) + " account(s)
")
            for i, acc in enumerate(accounts, 1):
                info = mgr.get_account_info(acc)
                status = info.get("status", "unknown")
                device = info.get("device_identity_summary", {})
                device_model = device.get("model", "unknown") if device else "unknown"
                print("  " + str(i) + ". @" + acc)
                print("     Status: " + status)
                print("     Device: " + device_model)

    except Exception as e:
        print("ERROR " + str(e))


def menu_statistics():
    """Show global statistics"""
    print("
" + "=" * 70)
    print("STATISTICS")
    print("=" * 70 + "
")

    try:
        mgr = AccountManager()
        stats = mgr.get_statistics()

        print("Total Accounts: " + str(stats.get('total_accounts', 0)))
        print("Active Accounts: " + str(stats.get('active_accounts', 0)))
        print("Verified Accounts: " + str(stats.get('verified_accounts', 0)))
        print("Blacklisted Accounts: " + str(stats.get('blacklisted_accounts', 0)))

        login_mgr = LoginManager()
        login_stats = login_mgr.get_login_statistics()
        print("
Active Sessions: " + str(login_stats.get('total_active_sessions', 0)))
        logged = ', '.join(login_stats.get('logged_in_accounts', [])) or 'None'
        print("Logged In: " + logged)

    except Exception as e:
        print("ERROR " + str(e))


def menu_run_tests():
    """Run unit tests"""
    print("
" + "=" * 70)
    print("RUNNING TEST SUITE")
    print("=" * 70 + "
")

    try:
        # Try import test suite
        from tests.test_all_modules import run_tests

        success = run_tests()
        if success:
            print("
SUCCESS All tests passed!")
        else:
            print("
ERROR Some tests failed.")
    except ImportError as e:
        print("ERROR Cannot import test suite: " + str(e))
    except Exception as e:
        print("ERROR Running tests: " + str(e))


def main():
    """Main entry"""
    try:
        show_banner()

        # Initial test
        if not test_modules():
            print("ERROR Core modules initialization failed.")
            sys.exit(1)

        # Show menu
        menu_main()

    except KeyboardInterrupt:
        print("

Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print("
ERROR Unexpected error: " + str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()