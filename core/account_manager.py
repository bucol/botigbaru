import json
import os
import datetime

class AccountManager:
    def __init__(self):
        # Kita simpan di folder data/ agar rapi
        self.data_dir = "data"
        self.db_file = os.path.join(self.data_dir, "accounts.json")
        self._setup()

    def _setup(self):
        """Memastikan folder dan file database tersedia"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        if not os.path.exists(self.db_file):
            # Inisialisasi list kosong []
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
        """Menambah atau mengupdate akun"""
        accounts = self.get_all_accounts()
        
        # Cek apakah username sudah ada (Update password kalau ada)
        found = False
        for acc in accounts:
            if acc['username'] == username:
                acc['password'] = password
                acc['updated_at'] = str(datetime.datetime.now())
                found = True
                break
        
        # Kalau belum ada, tambahkan baru
        if not found:
            accounts.append({
                "username": username,
                "password": password,
                "added_at": str(datetime.datetime.now())
            })
            
        self._save_db(accounts)
        print(f"✅ Akun {username} berhasil disimpan.")

    def delete_account(self, username):
        """Menghapus akun berdasarkan username"""
        accounts = self.get_all_accounts()
        new_accounts = [acc for acc in accounts if acc['username'] != username]
        
        if len(accounts) != len(new_accounts):
            self._save_db(new_accounts)
            print(f"🗑️ Akun {username} dihapus.")
            return True
        return False

    def _save_db(self, accounts):
        """Menulis kembali ke file JSON"""
        with open(self.db_file, 'w') as f:
            json.dump(accounts, f, indent=4)

# Test function kalau file ini dijalankan langsung
if __name__ == "__main__":
    am = AccountManager()
    print("Database Accounts:", am.get_all_accounts())