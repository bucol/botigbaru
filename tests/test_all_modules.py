#!/usr/bin/env python3
"""
Test Suite - Validasi Semua Modules

Run:
    python tests/test_all_modules.py
"""

import unittest
from pathlib import Path

from core.device_identity_generator import DeviceIdentityGenerator
from core.verification_handler import VerificationHandler, VerificationType
from core.session_manager_v2 import SessionManagerV2
from core.account_manager import AccountManager
from core.login_manager import LoginManager


class TestDeviceIdentityGenerator(unittest.TestCase):
    def setUp(self):
        self.gen = DeviceIdentityGenerator()

    def test_load_device_db(self):
        self.assertIsNotNone(self.gen.device_db)
        self.assertGreater(len(self.gen.device_db), 0)

    def test_generate_random_identity(self):
        identity = self.gen.generate_completely_random_identity()
        required_fields = [
            "device_id",
            "android_id",
            "gsf_id",
            "imei_1",
            "imei_2",
            "mac_wifi",
            "mac_bluetooth",
            "serial_number",
            "fingerprint",
            "brand",
            "manufacturer",
            "model",
        ]
        for field in required_fields:
            self.assertIn(field, identity)
            self.assertIsNotNone(identity[field])

    def test_identity_uniqueness(self):
        a = self.gen.generate_completely_random_identity()
        b = self.gen.generate_completely_random_identity()
        self.assertNotEqual(a["device_id"], b["device_id"])
        self.assertNotEqual(a["imei_1"], b["imei_1"])

    def test_save_load_delete_identity(self):
        username = "test_user_identity"
        identity = self.gen.generate_completely_random_identity()
        path = self.gen.save_identity(username, identity)
        self.assertTrue(Path(path).exists())

        loaded = self.gen.load_identity(username)
        self.assertIsNotNone(loaded)
        self.assertEqual(identity["device_id"], loaded["device_id"])

        deleted = self.gen.delete_identity(username)
        self.assertTrue(deleted)
        self.assertIsNone(self.gen.load_identity(username))

    def test_get_or_create_identity(self):
        username = "test_user_get_or_create"
        first = self.gen.get_or_create_identity(username)
        second = self.gen.get_or_create_identity(username)
        self.assertEqual(first["device_id"], second["device_id"])
        self.gen.delete_identity(username)


class TestVerificationHandler(unittest.TestCase):
    def setUp(self):
        self.handler = VerificationHandler()

    def test_detect_sms(self):
        is_verif, vtype = self.handler.detect_verification_required(
            "We sent a code via SMS to your phone"
        )
        self.assertTrue(is_verif)
        self.assertEqual(vtype, VerificationType.SMS)

    def test_detect_email(self):
        is_verif, vtype = self.handler.detect_verification_required(
            "Please confirm using the code sent to your email"
        )
        self.assertTrue(is_verif)
        self.assertEqual(vtype, VerificationType.EMAIL)

    def test_detect_2fa(self):
        is_verif, vtype = self.handler.detect_verification_required(
            "Two factor authentication required, open the authenticator app"
        )
        self.assertTrue(is_verif)
        self.assertEqual(vtype, VerificationType.TWO_FA)

    def test_log_and_retry_count(self):
        username = "test_verif_retry"
        for _ in range(3):
            self.handler.log_verification_attempt(
                username, VerificationType.SMS, "failed", code_used="123456"
            )
        retries = self.handler.get_retry_count(username)
        self.assertEqual(retries, 3)

    def test_blacklist(self):
        username = "test_blacklist"
        for _ in range(self.handler.max_retries):
            self.handler.log_verification_attempt(
                username, VerificationType.EMAIL, "failed"
            )
        self.assertTrue(self.handler.is_blacklisted(username))


class TestSessionManagerV2(unittest.TestCase):
    def setUp(self):
        self.mgr = SessionManagerV2()

    def test_create_save_load_clear_session(self):
        username = "test_session_user"
        device_identity = {
            "device_id": "test_device_id",
            "model": "SM-G991B",
            "android_version": 12,
        }
        session = self.mgr.create_session(username, device_identity)
        self.assertEqual(session["username"], username)
        self.assertIn("session_id", session)

        saved, path = self.mgr.save_session(username, session)
        self.assertTrue(saved)
        self.assertTrue(Path(path).exists())

        loaded = self.mgr.load_session(username)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["session_id"], session["session_id"])

        cleared, msg = self.mgr.clear_session(username)
        self.assertTrue(cleared)
        self.assertIsNone(self.mgr.load_session(username))

    def test_password_change_flow(self):
        username = "test_password_change"
        device_identity = {"device_id": "x", "model": "SM-G991B", "android_version": 12}
        session = self.mgr.create_session(username, device_identity)
        self.mgr.save_session(username, session)

        result = self.mgr.on_password_changed(username)
        self.assertTrue(result["success"])
        self.assertTrue(any(a["action"] == "session_cleared" for a in result["actions"]))


class TestAccountManager(unittest.TestCase):
    def setUp(self):
        self.mgr = AccountManager()

    def test_register_and_login_account(self):
        username = "test_register_login"
        password_hash = "pass_hash_123"

        ok, msg, result = self.mgr.register_account(username, password_hash)
        self.assertTrue(ok)
        self.assertIn(username, self.mgr.accounts_db)
        self.assertIn("device_identity", result)
        self.assertIn("session", result)

        ok_login, _, login_result = self.mgr.login_account(username, password_hash)
        self.assertTrue(ok_login)
        self.assertIn("session", login_result)

    def test_duplicate_register_blocked(self):
        username = "test_duplicate_register"
        pw = "x"
        ok1, _, _ = self.mgr.register_account(username, pw)
        self.assertTrue(ok1)
        ok2, msg2, _ = self.mgr.register_account(username, pw)
        self.assertFalse(ok2)
        self.assertIn("sudah terdaftar", msg2.lower())

    def test_change_password_flow(self):
        username = "test_change_password"
        pw_old = "old"
        pw_new = "new"

        self.mgr.register_account(username, pw_old)
        ok, msg, result = self.mgr.change_password(username, pw_new)
        self.assertTrue(ok)
        self.assertTrue(result["identity_deleted"])

    def test_get_account_info_and_stats(self):
        username = "test_info_stats"
        pw = "pw"
        self.mgr.register_account(username, pw)

        info = self.mgr.get_account_info(username)
        self.assertIsNotNone(info)
        self.assertEqual(info["username"], username)

        stats = self.mgr.get_statistics()
        self.assertIn("total_accounts", stats)


class TestLoginManager(unittest.TestCase):
    def setUp(self):
        self.mgr = LoginManager()

    def test_create_client(self):
        client = self.mgr.create_client()
        self.assertIsNotNone(client)

    def test_password_hashing(self):
        p = "secret_password"
        h1 = self.mgr._hash_password(p)
        h2 = self.mgr._hash_password(p)
        self.assertEqual(h1, h2)
        h3 = self.mgr._hash_password("other")
        self.assertNotEqual(h1, h3)

    def test_is_logged_in_flag(self):
        username = "test_flag"
        self.assertFalse(self.mgr.is_logged_in(username))
        self.mgr.active_clients[username] = None
        self.assertTrue(self.mgr.is_logged_in(username))
        del self.mgr.active_clients[username]
        self.assertFalse(self.mgr.is_logged_in(username))


class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.identity_gen = DeviceIdentityGenerator()
        self.verif = VerificationHandler()
        self.session_mgr = SessionManagerV2()
        self.account_mgr = AccountManager()
        self.login_mgr = LoginManager()

    def test_complete_workflow_register_info_stats(self):
        username = "test_complete_workflow"
        pw = "pw123"

        ok, msg, data = self.account_mgr.register_account(
            username, self.login_mgr._hash_password(pw)
        )
        self.assertTrue(ok)
        self.assertIn("device_identity", data)

        info = self.account_mgr.get_account_info(username)
        self.assertIsNotNone(info)
        self.assertEqual(info["username"], username)

        stats = self.account_mgr.get_statistics()
        self.assertGreaterEqual(stats["total_accounts"], 1)


def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDeviceIdentityGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestVerificationHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManagerV2))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManager))
    suite.addTests(loader.loadTestsFromTestCase(TestLoginManager))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTest))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    raise SystemExit(0 if success else 1)