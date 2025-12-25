# main.py - versi minimal aman

from core.device_identity_generator import DeviceIdentityGenerator
from core.verification_handler import VerificationHandler
from core.session_manager_v2 import SessionManagerV2
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