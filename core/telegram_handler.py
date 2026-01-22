import logging
# Placeholder agar tidak error saat diimport
class TelegramBotHandler:
    def __init__(self, controller):
        self.controller = controller
        self.logger = logging.getLogger(__name__)

    async def start(self):
        self.logger.warning("⚠️ Telegram Bot belum dikonfigurasi (Token kosong).")
        # Nanti kita isi logicnya kalau kamu sudah punya Token BotFather