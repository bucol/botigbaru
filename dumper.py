import os

# ================= KONFIGURASI =================
# Nama file hasil dump
# KODE INI UNTUK BACA SEMUA FILE DALAM FOLDER LO!
OUTPUT_FILE = "FULL_CODE_BOT_V2.txt"

# Folder yang mau DILEWATI (Gak usah di-dump)
IGNORED_DIRS = {
    '__pycache__', 
    '.git', 
    'venv', 
    'env', 
    '.idea', 
    '.vscode',
    'sessions', # PENTING: Folder session dilewati biar aman (isi password/cookie)
    'profile_pictures' # Folder gambar dilewati
}

# Ekstensi file yang mau DILEWATI (File binary/sampah)
IGNORED_EXTENSIONS = {
    '.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', 
    '.exe', '.dll', '.so', '.zip', '.rar', '.db', '.sqlite'
}

# ===============================================

def is_text_file(filename):
    """Cek apakah file aman untuk dibaca sebagai text"""
    return not any(filename.lower().endswith(ext) for ext in IGNORED_EXTENSIONS)

def dump_project():
    root_dir = os.getcwd() # Ambil direktori saat ini
    
    print(f"🚀 Memulai proses dumping dari: {root_dir}")
    print(f"📂 Folder diabaikan: {IGNORED_DIRS}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        # Header Utama
        outfile.write(f"# REPOSITORY DUMP\n")
        outfile.write(f"# Root: {root_dir}\n")
        outfile.write(f"# Generated: {os.path.basename(__file__)}\n\n")

        file_count = 0
        
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Filter folder yang diabaikan
            dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]
            
            for filename in filenames:
                # Skip file dumper ini sendiri dan file outputnya
                if filename in [os.path.basename(__file__), OUTPUT_FILE]:
                    continue
                
                # Skip file binary/gambar
                if not is_text_file(filename):
                    continue

                full_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_path, root_dir)
                
                try:
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        
                        # Tulis Header File
                        outfile.write("="*50 + "\n")
                        outfile.write(f"FILE PATH: {rel_path}\n")
                        outfile.write("="*50 + "\n")
                        
                        # Tulis Isi File
                        outfile.write(content + "\n\n")
                        
                        print(f"✅ Add: {rel_path}")
                        file_count += 1
                        
                except Exception as e:
                    print(f"❌ Gagal membaca {rel_path}: {e}")

    print("\n" + "="*30)
    print(f"🎉 SELESAI! {file_count} file berhasil di-dump.")
    print(f"📄 Cek file: {OUTPUT_FILE}")
    print("="*30)

if __name__ == "__main__":
    dump_project()