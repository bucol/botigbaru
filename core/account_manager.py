import json
import os
import datetime
import csv
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

class AccountManager:
    def __init__(self):
        self.data_dir = "data"
        self.db_file = os.path.join(self.data_dir, "accounts.json")
        self._setup()
        self._init_encryption()

    def _init_encryption(self):
        """Initialize encryption key"""
        key = os.getenv('ENCRYPTION_KEY')
        if key:
            # Pastikan key 32 bytes, encode ke base64
            key_bytes = key.encode()[:32].ljust(32, b'0')
            import base64
            self.cipher = Fernet(base64.urlsafe_b64encode(key_bytes))
        else:
            self.cipher = None
            print("ENCRYPTION_KEY tidak diset. Password akan disimpan terenkripsi dengan key default.")
            # Generate default key (untuk development only)
            default_key = Fernet.generate_key()
            self.cipher = Fernet(default_key)

    def _encrypt(self, text: str) -> str:
        """Encrypt text"""
        if self.cipher:
            return self.cipher.encrypt(text.encode()).decode()
        return text

    def _decrypt(self, encrypted_text: str) -> str:
        """Decrypt text"""
        if self.cipher:
            try:
                return self.cipher.decrypt(encrypted_text.encode()).decode()
            except:
                return encrypted_text  # Fallback jika gagal decrypt
        return encrypted_text

    def _setup(self):
        """Memastikan folder dan file database tersedia"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.db_file):
            with open(self.db_file, 'w') as f:
                json.dump([], f)

    def get_all_accounts(self):
        """Mengambil semua list akun"""
        try:
            with open(self.db_file, 'r') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def add_account(self, username, password):
        """Menambah atau mengupdate akun dengan password terenkripsi"""
        accounts = self.get_all_accounts()
        encrypted_password = self._encrypt(password)

        found = False
        for acc in accounts:
            if acc['username'] == username:
                acc['password'] = encrypted_password
                acc['updated_at'] = str(datetime.datetime.now())
                found = True
                break

        if not found:
            accounts.append({
                "username": username,
                "password": encrypted_password,
                "added_at": str(datetime.datetime.now())
            })

        self._save_db(accounts)

    def get_password(self, username):
        """Ambil password yang sudah didekripsi"""
        accounts = self.get_all_accounts()
        for acc in accounts:
            if acc['username'] == username:
                return self._decrypt(acc['password'])
        return None

    def _save_db(self, accounts):
        with open(self.db_file, 'w') as f:
            json.dump(accounts, f, indent=2)

    def export_to_csv(self, csv_file="accounts_export.csv"):
        """Export akun ke CSV (username,password decrypted)"""
        accounts = self.get_all_accounts()
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'password'])  # Header
            for acc in accounts:
                writer.writerow([acc['username'], self._decrypt(acc['password'])])
        print(f"Export berhasil ke {csv_file}")

    def import_from_csv(self, csv_file="accounts_import.csv"):
        """Import akun dari CSV, enkripsi password"""
        if not os.path.exists(csv_file):
            print(f"File {csv_file} tidak ada!")
            return
        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    self.add_account(row[0], row[1])
        print(f"Import dari {csv_file} berhasil!")

    def import_from_txt(self, txt_file="accounts.txt"):
        """Fitur baru: Bulk add dari TXT (format username:password per baris)"""
        if not os.path.exists(txt_file):
            print(f"File {txt_file} tidak ada!")
            return
        with open(txt_file, 'r') as f:
            for line in f:
                line = line.strip()
                if ':' in line:
                    username, password = line.split(':', 1)
                    self.add_account(username.strip(), password.strip())
        print(f"Bulk import dari {txt_file} berhasil!")

    @property
    def accounts_db(self):
        return self.get_all_accounts()