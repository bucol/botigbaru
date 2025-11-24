#!/usr/bin/env python3
"""
Reset Password Instagram - Manual Code Input
User menerima kode dari email/SMS dan input secara manual
"""

from banner import show_separator, success_msg, error_msg, info_msg, warning_msg
from colorama import Fore, Style

def reset_password(client, username):
    """Reset password Instagram dengan input kode manual"""
    show_separator()
    print(Fore.CYAN + "\n🔑 RESET PASSWORD INSTAGRAM" + Style.RESET_ALL)
    show_separator()

    try:
        warning_msg("Fitur reset password akan mengirim kode ke email atau SMS akun")
        
        print(Fore.YELLOW + "\n📌 LANGKAH-LANGKAH:")
        print("   1. Instagram akan kirim kode ke email atau no HP akun")
        print("   2. Cek email atau SMS untuk kode reset")
        print("   3. Input kode yang diterima di sini")
        print("   4. Buat password baru" + Style.RESET_ALL)

        confirm = input(Fore.MAGENTA + "\nLanjutkan reset password? (yes/no): " + Style.RESET_ALL).strip().lower()
        if confirm != "yes":
            info_msg("Reset password dibatalkan")
            return

        print(Fore.YELLOW + "\n" + "="*63)
        print("📧 MENGIRIM KODE RESET KE EMAIL/SMS")
        print("="*63 + Style.RESET_ALL)

        try:
            # Request reset password ke Instagram
            info_msg("Mengirim request reset password ke Instagram...")
            result = client.private_request(
                "accounts/send_recovery_flow_email/",
                data={}
            )
            
            success_msg("✅ Kode reset telah dikirim ke email/SMS akun!")
            
        except Exception as e:
            warning_msg(f"Method 1 error: {str(e)}")
            info_msg("Mencoba method alternatif...")
            
            try:
                # Method alternatif
                client.private_request(
                    "accounts/send_recovery_email/",
                    data={"email_or_username": username}
                )
                success_msg("✅ Kode reset telah dikirim!")
            except Exception as e2:
                error_msg(f"Gagal mengirim kode reset: {str(e2)}")
                warning_msg("Silakan reset password manual di aplikasi Instagram atau website")
                return

        # Minta user input kode
        print(Fore.YELLOW + "\n" + "="*63)
        print("🔐 MASUKKAN KODE RESET")
        print("="*63 + Style.RESET_ALL)

        code = input(Fore.YELLOW + "\nMasukkan kode reset (dari email/SMS): " + Style.RESET_ALL).strip()
        if not code:
            error_msg("Kode reset tidak boleh kosong!")
            return

        # Minta password baru
        new_password = input(Fore.YELLOW + "Password baru: " + Style.RESET_ALL).strip()
        if not new_password or len(new_password) < 6:
            error_msg("Password minimal 6 karakter!")
            return

        confirm_password = input(Fore.YELLOW + "Konfirmasi password baru: " + Style.RESET_ALL).strip()
        if new_password != confirm_password:
            error_msg("Password tidak cocok!")
            return

        # Kirim kode dan password baru ke Instagram
        info_msg("Memproses reset password...")

        try:
            result = client.private_request(
                "accounts/change_password/",
                data={
                    "old_password": "",
                    "new_password1": new_password,
                    "new_password2": new_password,
                    "code": code
                }
            )

            if result:
                success_msg("✅ Password berhasil direset! 🎉")
                success_msg(f"Gunakan password baru untuk login berikutnya")
                warning_msg("Silakan logout dan login kembali dengan password baru")
            else:
                error_msg("Reset password gagal!")

        except Exception as e:
            error_msg(f"Error saat reset password: {str(e)}")
            warning_msg("Kemungkinan kode salah atau sudah expired (coba lagi 5 menit)")

    except Exception as e:
        error_msg(f"Error: {str(e)}")

    input(Fore.CYAN + "\nTekan Enter untuk kembali..." + Style.RESET_ALL)
