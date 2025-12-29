"""
Telegram Command Handler
Control bot via Telegram commands
"""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ python-telegram-bot tidak terinstall. Jalankan: pip install python-telegram-bot")

class TelegramBotHandler:
    def __init__(self, bot_controller=None):
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.bot_controller = bot_controller
        self.application = None
        self.is_running = False
        
        if not self.token:
            print("❌ TELEGRAM_TOKEN tidak ditemukan di .env")
        if not self.chat_id:
            print("⚠️ TELEGRAM_CHAT_ID tidak ditemukan di .env")
    
    def set_controller(self, controller):
        """Set bot controller untuk akses fitur"""
        self.bot_controller = controller
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /start"""
        keyboard = [
            [
                InlineKeyboardButton("📊 Status", callback_data="status"),
                InlineKeyboardButton("📈 Stats", callback_data="stats")
            ],
            [
                InlineKeyboardButton("👥 Accounts", callback_data="accounts"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings")
            ],
            [
                InlineKeyboardButton("❤️ Auto Like", callback_data="autolike"),
                InlineKeyboardButton("👤 Auto Follow", callback_data="autofollow")
            ],
            [
                InlineKeyboardButton("💬 Auto Comment", callback_data="autocomment"),
                InlineKeyboardButton("🎯 Scrape", callback_data="scrape")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        welcome_text = """
🤖 *Instagram Bot Controller*

Selamat datang! Gunakan menu di bawah atau command berikut:

📊 *Status & Info*
/status - Cek status bot
/stats - Lihat statistik
/accounts - Daftar akun

❤️ *Auto Actions*
/like <hashtag> <jumlah> - Auto like
/follow <username> <jumlah> - Auto follow
/comment <hashtag> <jumlah> - Auto comment
/unfollow <jumlah> - Unfollow non-followers

🎯 *Target Scraping*
/scrape followers <username> <jumlah>
/scrape hashtag <hashtag> <jumlah>
/scrape likers <post_url> <jumlah>

⚙️ *Settings*
/setdelay <min> <max> - Set delay
/setlimit <action> <limit> - Set daily limit
/pause - Pause semua action
/resume - Resume action
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /status"""
        status_text = "📊 *Bot Status*\n\n"
        
        if self.bot_controller:
            # Dapatkan status dari controller
            accounts = self.bot_controller.get("accounts", [])
            scheduler = self.bot_controller.get("scheduler")
            
            status_text += f"👥 Akun Aktif: {len(accounts)}\n"
            
            if scheduler:
                stats = scheduler.get_stats()
                status_text += f"📋 Queue: {stats.get('queue_size', 0)} tasks\n"
                status_text += f"⏸️ Paused: {'Ya' if stats.get('paused', False) else 'Tidak'}\n"
            
            status_text += f"\n🕐 Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            status_text += "⚠️ Bot controller tidak terhubung"
        
        await update.message.reply_text(status_text, parse_mode="Markdown")
    
    async def stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /stats"""
        stats_text = "📈 *Statistik Hari Ini*\n\n"
        
        if self.bot_controller:
            analytics = self.bot_controller.get("analytics")
            
            if analytics:
                daily = analytics.get_daily_stats()
                stats_text += f"❤️ Likes: {daily.get('like', {}).get('success', 0)}\n"
                stats_text += f"👤 Follows: {daily.get('follow', {}).get('success', 0)}\n"
                stats_text += f"💬 Comments: {daily.get('comment', {}).get('success', 0)}\n"
                stats_text += f"👋 Unfollows: {daily.get('unfollow', {}).get('success', 0)}\n"
                stats_text += f"📩 DMs: {daily.get('dm', {}).get('success', 0)}\n"
                stats_text += f"👁️ Story Views: {daily.get('story_view', {}).get('success', 0)}\n"
            else:
                stats_text += "📊 Analytics tidak tersedia"
        else:
            stats_text += "⚠️ Bot controller tidak terhubung"
        
        await update.message.reply_text(stats_text, parse_mode="Markdown")
    
    async def accounts(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /accounts"""
        accounts_text = "👥 *Daftar Akun*\n\n"
        
        if self.bot_controller:
            accounts = self.bot_controller.get("accounts", [])
            
            if accounts:
                for i, acc in enumerate(accounts, 1):
                    status_emoji = "✅" if acc.get("active", False) else "❌"
                    accounts_text += f"{i}. {status_emoji} @{acc.get('username', 'unknown')}\n"
            else:
                accounts_text += "Belum ada akun terdaftar"
        else:
            accounts_text += "⚠️ Bot controller tidak terhubung"
        
        await update.message.reply_text(accounts_text, parse_mode="Markdown")
    
    async def like_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /like <hashtag> <amount>"""
        args = context.args
        
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Format: /like <hashtag> [jumlah]\n"
                "Contoh: /like photography 10"
            )
            return
        
        hashtag = args[0].lstrip("#")
        amount = int(args[1]) if len(args) > 1 else 10
        
        await update.message.reply_text(
            f"⏳ Memulai auto like #{hashtag} ({amount} posts)..."
        )
        
        if self.bot_controller:
            auto_like = self.bot_controller.get("auto_like")
            if auto_like:
                results = auto_like.like_by_hashtag(hashtag, amount)
                
                await update.message.reply_text(
                    f"✅ *Auto Like Selesai*\n\n"
                    f"✅ Success: {results['success']}\n"
                    f"❌ Failed: {results['failed']}\n"
                    f"⏭️ Skipped: {results['skipped']}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Auto Like module tidak tersedia")
        else:
            await update.message.reply_text("❌ Bot controller tidak terhubung")
    
    async def follow_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /follow <username/hashtag> <amount>"""
        args = context.args
        
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Format: /follow <username/hashtag> [jumlah]\n"
                "Contoh:\n"
                "  /follow @targetuser 10\n"
                "  /follow #photography 10"
            )
            return
        
        target = args[0]
        amount = int(args[1]) if len(args) > 1 else 10
        
        await update.message.reply_text(
            f"⏳ Memulai auto follow dari {target} ({amount} users)..."
        )
        
        if self.bot_controller:
            auto_follow = self.bot_controller.get("auto_follow")
            if auto_follow:
                if target.startswith("#"):
                    results = auto_follow.follow_by_hashtag(target, amount)
                else:
                    results = auto_follow.follow_followers_of(target, amount)
                
                await update.message.reply_text(
                    f"✅ *Auto Follow Selesai*\n\n"
                    f"✅ Success: {results['success']}\n"
                    f"❌ Failed: {results['failed']}\n"
                    f"⏭️ Skipped: {results['skipped']}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Auto Follow module tidak tersedia")
        else:
            await update.message.reply_text("❌ Bot controller tidak terhubung")
    
    async def comment_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /comment <hashtag> <amount>"""
        args = context.args
        
        if len(args) < 1:
            await update.message.reply_text(
                "❌ Format: /comment <hashtag/username> [jumlah]\n"
                "Contoh: /comment #photography 5"
            )
            return
        
        target = args[0]
        amount = int(args[1]) if len(args) > 1 else 5
        
        await update.message.reply_text(
            f"⏳ Memulai auto comment pada {target} ({amount} posts)..."
        )
        
        if self.bot_controller:
            auto_comment = self.bot_controller.get("auto_comment")
            if auto_comment:
                if target.startswith("#"):
                    results = auto_comment.comment_by_hashtag(target, amount)
                else:
                    results = auto_comment.comment_user_posts(target, amount)
                
                comments_preview = "\n".join([
                    f"• {c['comment']}" for c in results.get('comments', [])[:3]
                ])
                
                await update.message.reply_text(
                    f"✅ *Auto Comment Selesai*\n\n"
                    f"✅ Success: {results['success']}\n"
                    f"❌ Failed: {results['failed']}\n"
                    f"⏭️ Skipped: {results['skipped']}\n\n"
                    f"💬 Comments:\n{comments_preview}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Auto Comment module tidak tersedia")
        else:
            await update.message.reply_text("❌ Bot controller tidak terhubung")
    
    async def unfollow_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /unfollow <amount>"""
        args = context.args
        amount = int(args[0]) if args else 10
        
        await update.message.reply_text(
            f"⏳ Memulai unfollow non-followers ({amount} users)..."
        )
        
        if self.bot_controller:
            auto_follow = self.bot_controller.get("auto_follow")
            if auto_follow:
                results = auto_follow.unfollow_non_followers(amount)
                
                await update.message.reply_text(
                    f"✅ *Unfollow Selesai*\n\n"
                    f"✅ Success: {results['success']}\n"
                    f"❌ Failed: {results['failed']}\n"
                    f"⏭️ Skipped: {results['skipped']}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Auto Follow module tidak tersedia")
        else:
            await update.message.reply_text("❌ Bot controller tidak terhubung")
    
    async def scrape_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /scrape <type> <target> <amount>"""
        args = context.args
        
        if len(args) < 2:
            await update.message.reply_text(
                "❌ Format: /scrape <type> <target> [jumlah]\n\n"
                "Types:\n"
                "• followers <username> - Scrape followers\n"
                "• following <username> - Scrape following\n"
                "• hashtag <hashtag> - Scrape dari hashtag\n"
                "• likers <post_code> - Scrape likers\n"
                "• commenters <post_code> - Scrape commenters\n\n"
                "Contoh: /scrape followers @targetuser 100"
            )
            return
        
        scrape_type = args[0].lower()
        target = args[1]
        amount = int(args[2]) if len(args) > 2 else 50
        
        await update.message.reply_text(
            f"⏳ Memulai scrape {scrape_type} dari {target}..."
        )
        
        if self.bot_controller:
            scraper = self.bot_controller.get("scraper")
            if scraper:
                if scrape_type == "followers":
                    results = scraper.scrape_followers(target, amount)
                elif scrape_type == "following":
                    results = scraper.scrape_following(target, amount)
                elif scrape_type == "hashtag":
                    results = scraper.scrape_hashtag_users(target, amount)
                elif scrape_type == "likers":
                    results = scraper.scrape_likers(target, amount)
                elif scrape_type == "commenters":
                    results = scraper.scrape_commenters(target, amount)
                else:
                    await update.message.reply_text(f"❌ Unknown type: {scrape_type}")
                    return
                
                await update.message.reply_text(
                    f"✅ *Scrape Selesai*\n\n"
                    f"📊 Total: {results.get('total', 0)} users\n"
                    f"💾 Saved to: {results.get('file', 'N/A')}",
                    parse_mode="Markdown"
                )
            else:
                await update.message.reply_text("❌ Scraper module tidak tersedia")
        else:
            await update.message.reply_text("❌ Bot controller tidak terhubung")
    
    async def pause_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /pause"""
        if self.bot_controller:
            scheduler = self.bot_controller.get("scheduler")
            if scheduler:
                scheduler.pause()
                await update.message.reply_text("⏸️ Bot di-pause. Gunakan /resume untuk melanjutkan.")
            else:
                await update.message.reply_text("❌ Scheduler tidak tersedia")
        else:
            await update.message.reply_text("❌ Bot controller tidak terhubung")
    
    async def resume_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk /resume"""
        if self.bot_controller:
            scheduler = self.bot_controller.get("scheduler")
            if scheduler:
                scheduler.resume()
                await update.message.reply_text("▶️ Bot di-resume. Actions akan dilanjutkan.")
            else:
                await update.message.reply_text("❌ Scheduler tidak tersedia")
        else:
            await update.message.reply_text("❌ Bot controller tidak terhubung")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler untuk inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        callback_map = {
            "status": self._show_status,
            "stats": self._show_stats,
            "accounts": self._show_accounts,
            "settings": self._show_settings,
            "autolike": self._show_autolike_menu,
            "autofollow": self._show_autofollow_menu,
            "autocomment": self._show_autocomment_menu,
            "scrape": self._show_scrape_menu
        }
        
        handler = callback_map.get(query.data)
        if handler:
            await handler(query)
        else:
            await query.edit_message_text("❌ Unknown action")
    
    async def _show_status(self, query):
        """Tampilkan status"""
        status_text = "📊 *Bot Status*\n\n"
        status_text += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        status_text += "✅ Bot aktif dan berjalan"
        
        keyboard = [[InlineKeyboardButton("◀️ Back", callback_data="back_main")]]
        await query.edit_message_text(
            status_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def _show_stats(self, query):
        """Tampilkan statistik"""
        await query.edit_message_text(
            "📈 *Statistik*\n\nGunakan /stats untuk melihat statistik lengkap.",
            parse_mode="Markdown"
        )
    
    async def _show_accounts(self, query):
        """Tampilkan daftar akun"""
        await query.edit_message_text(
            "👥 *Accounts*\n\nGunakan /accounts untuk melihat daftar akun.",
            parse_mode="Markdown"
        )
    
    async def _show_settings(self, query):
        """Tampilkan settings menu"""
        keyboard = [
            [
                InlineKeyboardButton("⏱️ Delay", callback_data="set_delay"),
                InlineKeyboardButton("📊 Limits", callback_data="set_limits")
            ],
            [InlineKeyboardButton("◀️ Back", callback_data="back_main")]
        ]
        await query.edit_message_text(
            "⚙️ *Settings*\n\nPilih setting yang ingin diubah:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    async def _show_autolike_menu(self, query):
        """Tampilkan auto like menu"""
        await query.edit_message_text(
            "❤️ *Auto Like*\n\n"
            "Gunakan command:\n"
            "/like <hashtag> [jumlah]\n\n"
            "Contoh: /like photography 10",
            parse_mode="Markdown"
        )
    
    async def _show_autofollow_menu(self, query):
        """Tampilkan auto follow menu"""
        await query.edit_message_text(
            "👤 *Auto Follow*\n\n"
            "Gunakan command:\n"
            "/follow <username> [jumlah]\n"
            "/unfollow [jumlah]\n\n"
            "Contoh: /follow @targetuser 10",
            parse_mode="Markdown"
        )
    
    async def _show_autocomment_menu(self, query):
        """Tampilkan auto comment menu"""
        await query.edit_message_text(
            "💬 *Auto Comment*\n\n"
            "Gunakan command:\n"
            "/comment <hashtag/username> [jumlah]\n\n"
            "Contoh: /comment #photography 5",
            parse_mode="Markdown"
        )
    
    async def _show_scrape_menu(self, query):
        """Tampilkan scrape menu"""
        await query.edit_message_text(
            "🎯 *Target Scraper*\n\n"
            "Gunakan command:\n"
            "/scrape followers <username> [jumlah]\n"
            "/scrape hashtag <hashtag> [jumlah]\n"
            "/scrape likers <post_code> [jumlah]\n\n"
            "Contoh: /scrape followers @competitor 100",
            parse_mode="Markdown"
        )
    
    def run(self):
        """Jalankan Telegram bot"""
        if not TELEGRAM_AVAILABLE:
            print("❌ python-telegram-bot tidak tersedia")
            return
        
        if not self.token:
            print("❌ TELEGRAM_TOKEN tidak ditemukan")
            return
        
        print("🚀 Starting Telegram Bot Handler...")
        
        self.application = Application.builder().token(self.token).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("status", self.status))
        self.application.add_handler(CommandHandler("stats", self.stats))
        self.application.add_handler(CommandHandler("accounts", self.accounts))
        self.application.add_handler(CommandHandler("like", self.like_command))
        self.application.add_handler(CommandHandler("follow", se