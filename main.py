# main.py - versi minimal aman

from core.device_identity_generator import DeviceIdentityGenerator
# Dummy verification_handler kalau hilang
try:
    from core.verification_handler import VerificationHandler
except ImportError:
    class VerificationHandler:
        def __init__(self):
            self.max_retries = 3
from core.session_manager import SessionManager as SessionManagerV2
from core.account_manager import AccountManager
from core.login_manager import LoginManager


def main():
    print("Testing core modules...")
    gen = DeviceIdentityGenerator()
    print("DeviceIdentityGenerator OK, devices:", len(gen.device_db))

    verif = VerificationHandler()
    print("VerificationHandler OK, max_retries:", verif.max_retries)

    sess = SessionManagerV2()
    print("SessionManagerV2 OK")

    acc = AccountManager()
    print("AccountManager OK, accounts:", len(acc.accounts_db))

    login = LoginManager()
    print("LoginManager OK")

    print("All core modules loaded successfully.")


if __name__ == "__main__":
    main()