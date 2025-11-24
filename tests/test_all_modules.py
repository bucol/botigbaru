#!/usr/bin/env python3
"""
Test Suite - Validasi Semua Modules
Test: Device Identity, Verification, Session, Account Manager, Login Manager
Production-grade testing dengan detailed reporting
"""

import json
import unittest
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Import all modules
from core.device_identity_generator import DeviceIdentityGenerator
from core.verification_handler import VerificationHandler, VerificationType
from core.session_manager_v2 import SessionManagerV2
from core.account_manager import AccountManager
from core.login_manager import LoginManager

class TestDeviceIdentityGenerator(unittest.TestCase):
    """Test Device Identity Generator"""
    
    def setUp(self):
        self.gen = DeviceIdentityGenerator()
    
    def test_load_device_db(self):
        """Test load device database"""
        self.assertIsNotNone(self.gen.device_db)
        self.assertGreater(len(self.gen.device_db), 0)
        print(f"✅ Device DB loaded: {len(self.gen.device_db)} devices")
    
    def test_generate_random_identity(self):
        """Test generate completely random identity"""
        identity = self.gen.generate_completely_random_identity()
        
        # Validate required fields
        required_fields = [
            'device_id', 'android_id', 'gsf_id', 'imei_1', 'imei_2',
            'mac_wifi', 'mac_bluetooth', 'serial_number', 'fingerprint',
            'brand', 'manufacturer', 'model'
        ]
        
        for field in required_fields:
            self.assertIn(field, identity)
            self.assertIsNotNone(identity[field])
        
        print(f"✅ Random identity generated: {identity.get('model')}")
    
    def test_identity_uniqueness(self):
        """Test bahwa generated identities unik"""
        identity1 = self.gen.generate_completely_random_identity()
        identity2 = self.gen.generate_completely_random_identity()
        
        # Device IDs harus beda
        self.assertNotEqual(
            identity1.get('device_id'),
            identity2.get('device_id')
        )
        
        # IMEI harus beda
        self.assertNotEqual(
            identity1.get('imei_1'),
            identity2.get('imei_1')
        )
        
        print(f"✅ Uniqueness verified: ID1 != ID2")
    
    def test_save_load_identity(self):
        """Test save dan load identity"""
        username = "test_user_identity"
        identity = self.gen.generate_completely_random_identity()
        
        # Save
        filepath = self.gen.save_identity(username, identity)
        self.assertTrue(Path(filepath).exists())
        
        # Load
        loaded = self.gen.load_identity(username)
        self.assertIsNotNone(loaded)
        self.assertEqual(
            identity.get('device_id'),
            loaded.get('device_id')
        )
        
        # Cleanup
        self.gen.delete_identity(username)
        self.assertIsNone(self.gen.load_identity(username))
        
        print(f"✅ Save/Load/Delete identity: SUCCESS")
    
    def test_get_or_create_identity(self):
        """Test get existing atau create baru"""
        username = "test_user_getorcreate"
        
        # Create baru
        identity1 = self.gen.get_or_create_identity(username)
        self.assertIsNotNone(identity1)
        
        # Get existing (harus sama)
        identity2 = self.gen.get_or_create_identity(username)
        self.assertEqual(
            identity1.get('device_id'),
            identity2.get('device_id')
        )
        
        # Cleanup
        self.gen.delete_identity(username)
        
        print(f"✅ Get/Create identity: SUCCESS")


class TestVerificationHandler(unittest.TestCase):
    """Test Verification Handler"""
    
    def setUp(self):
        self.handler = VerificationHandler()
    
    def test_detect_verification_sms(self):
        """Test detect SMS verification"""
        is_verif, verif_type = self.handler.detect_verification_required(
            "Please verify via SMS code sent to your phone"
        )
        
        self.assertTrue(is_verif)
        self.assertEqual(verif_type, VerificationType.SMS)
        
        print(f"✅ SMS verification detected")
    
    def test_detect_verification_checkpoint(self):
        """Test detect checkpoint"""
        is_verif, verif_type = self.handler.detect_verification_required(
            "Unusual activity detected, checkpoint required"
        )
        
        self.assertTrue(is_verif)
        self.assertEqual(verif_type, VerificationType.CHECKPOINT)
        
        print(f"✅ Checkpoint verification detected")
    
    def test_detect_verification_2fa(self):
        """Test detect 2FA"""
        is_verif, verif_type = self.handler.detect_verification_required(
            "Two factor authentication required, enter code from authenticator"
        )
        
        self.assertTrue(is_verif)
        self.assertEqual(verif_type, VerificationType.TWO_FA)
        
        print(f"✅ 2FA verification detected")
    
    def test_log_verification_attempt(self):
        """Test log verification attempt"""
        username = "test_verification"
        entry = self.handler.log_verification_attempt(
            username, VerificationType.SMS, 'success', '123456'
        )
        
        self.assertEqual(entry['username'], username)
        self.assertEqual(entry['status'], 'success')
        
        print(f"✅ Verification attempt logged")
    
    def test_retry_counting(self):
        """Test retry count tracking"""
        username = "test_retry_count"
        
        # Log multiple failures
        for i in range(3):
            self.handler.log_verification_attempt(
                username, VerificationType.EMAIL, 'failed', f'code{i}'
            )
        
        retry_count = self.handler.get_retry_count(username)
        self.assertEqual(retry_count, 3)
        
        print(f"✅ Retry count tracked: {retry_count} attempts")
    
    def test_blacklist_system(self):
        """Test blacklist on max retries"""
        username = "test_blacklist"
        
        # Log 5 failures
        for i in range(5):
            self.handler.log_verification_attempt(
                username, VerificationType.SMS, 'failed'
            )
        
        is_blacklisted = self.handler.is_blacklisted(username)
        self.assertTrue(is_blacklisted)
        
        print(f"✅ Blacklist system working: {username} blacklisted")


class TestSessionManager(unittest.TestCase):
    """Test Session Manager v2"""
    
    def setUp(self):
        self.mgr = SessionManagerV2()
    
    def test_create_session(self):
        """Test create session"""
        username = "test_session"
        device_identity = {
            'device_id': 'test_device_123',
            'android_id': 'test_android_456',
            'model': 'SM-G991B',
            'manufacturer': 'Samsung'
        }
        
        session = self.mgr.create_session(username, device_identity)
        
        self.assertIsNotNone(session)
        self.assertEqual(session['username'], username)
        self.assertIn('session_id', session)
        self.assertIn('instagrapi_config', session)
        
        print(f"✅ Session created: {session['session_id']}")
    
    def test_save_load_session(self):
        """Test save dan load session"""
        username = "test_save_load"
        device_identity = {'device_id': 'test', 'model': 'test_model'}
        
        # Create dan save
        session = self.mgr.create_session(username, device_identity)
        saved, filepath = self.mgr.save_session(username, session)
        
        self.assertTrue(saved)
        self.assertTrue(Path(filepath).exists())
        
        # Load
        loaded = self.mgr.load_session(username)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded['session_id'], session['session_id'])
        
        # Clear
        cleared, msg = self.mgr.clear_session(username)
        self.assertTrue(cleared)
        self.assertIsNone(self.mgr.load_session(username))
        
        print(f"✅ Save/Load/Clear session: SUCCESS")
    
    def test_password_change_flow(self):
        """Test auto clear on password change"""
        username = "test_password_change"
        device_identity = {'device_id': 'test', 'model': 'test_model'}
        
        # Create session
        session = self.mgr.create_session(username, device_identity)
        self.mgr.save_session(username, session)
        
        # Trigger password change
        result = self.mgr.on_password_changed(username)
        
        self.assertTrue(result['success'])
        self.assertIn('session_cleared', [a.get('action') for a in result['actions']])
        self.assertIn('identity_cleared', [a.get('action') for a in result['actions']])
        
        print(f"✅ Password change flow: {len(result['actions'])} actions")


class TestAccountManager(unittest.TestCase):
    """Test Account Manager"""
    
    def setUp(self):
        self.mgr = AccountManager()
    
    def test_register_account(self):
        """Test register new account"""
        username = "test_register_account"
        password_hash = "hashed_password_123"
        email = "test@email.com"
        
        success, msg, result = self.mgr.register_account(username, password_hash, email)
        
        self.assertTrue(success)
        self.assertIn(username, self.mgr.accounts_db)
        self.assertIn('device_identity', result)
        self.assertIn('session', result)
        
        print(f"✅ Account registered: {username}")
    
    def test_account_duplicate_check(self):
        """Test duplicate account prevention"""
        username = "test_duplicate"
        password_hash = "pass123"
        
        # Register first time
        success1, _, _ = self.mgr.register_account(username, password_hash)
        self.assertTrue(success1)
        
        # Try register again (should fail)
        success2, msg, _ = self.mgr.register_account(username, password_hash)
        self.assertFalse(success2)
        self.assertIn("sudah terdaftar", msg.lower())
        
        print(f"✅ Duplicate check working")
    
    def test_login_account(self):
        """Test login existing account"""
        username = "test_login_account"
        password_hash = "pass123"
        
        # Register
        self.mgr.register_account(username, password_hash)
        
        # Login
        success, msg, result = self.mgr.login_account(username, password_hash)
        
        self.assertTrue(success)
        self.assertIn('device_identity', result)
        self.assertIn('session', result)
        
        print(f"✅ Account login: SUCCESS")
    
    def test_get_account_info(self):
        """Test get account info"""
        username = "test_account_info"
        password_hash = "pass123"
        
        # Register
        self.mgr.register_account(username, password_hash)
        
        # Get info
        info = self.mgr.get_account_info(username)
        
        self.assertIsNotNone(info)
        self.assertEqual(info['username'], username)
        self.assertIn('device_identity_summary', info)
        self.assertIn('verification_stats', info)
        
        print(f"✅ Account info retrieved")
    
    def test_list_accounts(self):
        """Test list all accounts"""
        # Register beberapa akun
        for i in range(3):
            self.mgr.register_account(f"test_list_{i}", f"pass{i}")
        
        accounts = self.mgr.list_all_accounts()
        
        self.assertGreaterEqual(len(accounts), 3)
        
        print(f"✅ Listed {len(accounts)} accounts")
    
    def test_get_statistics(self):
        """Test get global statistics"""
        stats = self.mgr.get_statistics()
        
        self.assertIn('total_accounts', stats)
        self.assertIn('active_accounts', stats)
        self.assertIn('verified_accounts', stats)
        self.assertGreater(stats['total_accounts'], 0)
        
        print(f"✅ Statistics: {stats['total_accounts']} total accounts")


class TestLoginManager(unittest.TestCase):
    """Test Login Manager"""
    
    def setUp(self):
        self.mgr = LoginManager()
    
    def test_create_client(self):
        """Test create instagrapi client"""
        client = self.mgr.create_client()
        
        self.assertIsNotNone(client)
        
        print(f"✅ Client created successfully")
    
    def test_password_hashing(self):
        """Test password hashing"""
        password = "test_password_123"
        
        hash1 = self.mgr._hash_password(password)
        hash2 = self.mgr._hash_password(password)
        
        # Same password = same hash
        self.assertEqual(hash1, hash2)
        
        # Different password = different hash
        hash3 = self.mgr._hash_password("different_password")
        self.assertNotEqual(hash1, hash3)
        
        print(f"✅ Password hashing working")
    
    def test_is_logged_in(self):
        """Test logged in check"""
        username = "test_login_check"
        
        # Not logged in yet
        self.assertFalse(self.mgr.is_logged_in(username))
        
        # Simulate login
        self.mgr.active_clients[username] = None  # Dummy client
        self.assertTrue(self.mgr.is_logged_in(username))
        
        # Logout
        del self.mgr.active_clients[username]
        self.assertFalse(self.mgr.is_logged_in(username))
        
        print(f"✅ Login status check working")


class IntegrationTest(unittest.TestCase):
    """Integration tests untuk semua modules bekerja sama"""
    
    def setUp(self):
        self.identity_gen = DeviceIdentityGenerator()
        self.verification = VerificationHandler()
        self.session_mgr = SessionManagerV2()
        self.account_mgr = AccountManager()
        self.login_mgr = LoginManager()
    
    def test_complete_workflow(self):
        """Test complete workflow: register -> login -> verify -> info"""
        username = "test_complete_workflow"
        password = "test_password_123"
        
        print(f"\n🔄 Testing complete workflow...")
        
        # Step 1: Register
        print(f"  1. Registering...")
        reg_ok, reg_msg, reg_data = self.account_mgr.register_account(
            username, self.login_mgr._hash_password(password)
        )
        self.assertTrue(reg_ok)
        self.assertIn('device_identity', reg_data)
        print(f"     ✅ Registered")
        
        # Step 2: Get device info
        device = reg_data['device_identity']
        self.assertIn('device_id', device)
        self.assertIn('android_id', device)
        self.assertIn('gsf_id', device)
        print(f"     ✅ Device identity: {device.get('model')}")
        
        # Step 3: Get account info
        info = self.account_mgr.get_account_info(username)
        self.assertIsNotNone(info)
        self.assertEqual(info['status'], 'active')
        print(f"     ✅ Account info retrieved")
        
        # Step 4: Stats
        stats = self.account_mgr.get_statistics()
        self.assertGreater(stats['total_accounts'], 0)
        print(f"     ✅ Statistics: {stats['total_accounts']} total")
        
        print(f"  ✅ Complete workflow SUCCESS\n")


def run_tests():
    """Run all tests dengan detailed reporting"""
    
    print("\n" + "="*70)
    print("🧪 BUCOL BOT TEST SUITE - ALL MODULES")
    print("="*70 + "\n")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestDeviceIdentityGenerator))
    suite.addTests(loader.loadTestsFromTestCase(TestVerificationHandler))
    suite.addTests(loader.loadTestsFromTestCase(TestSessionManager))
    suite.addTests(loader.loadTestsFromTestCase(TestAccountManager))
    suite.addTests(loader.loadTestsFromTestCase(TestLoginManager))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTest))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print(f"\n✅ ALL TESTS PASSED! 🎉")
    else:
        print(f"\n❌ Some tests failed. Review above.")
    
    print("="*70 + "\n")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
