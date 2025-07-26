from app.utils.logger import get_logger
from app.utils.command import handle_command
from app.utils.api import telegram_post, telegram_get
from app.core.config import settings
from app.schema.webhook import Update

logger = get_logger(__name__)

class TelegramService:
    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def set_webhook(self, webhook_url: str) -> bool:
        url = f"{self.base_url}/setWebhook"
        data = {
            "url": webhook_url,
            "allowed_updates": ["message", "callback_query"]
        }
        try:
            result = await telegram_post(url, data)
            if result.get("ok"):
                logger.info(f"Webhook set successfully: {webhook_url}")
                return True
            else:
                logger.error(f"Failed to set webhook: {result}")
                return False
        except Exception as e:
            logger.error(f"Error setting webhook: {e}")
            return False

    async def get_webhook_info(self) -> dict:
        url = f"{self.base_url}/getWebhookInfo"
        try:
            return await telegram_get(url)
        except Exception as e:
            logger.error(f"Error getting webhook info: {e}")
            return {}

    async def send_message(self, chat_id: int, text: str, parse_mode: str = "Markdown", reply_markup=None) -> bool:
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode
        }

        if reply_markup:
            data["reply_markup"] = reply_markup

        try:
            result = await telegram_post(url, data)
            return result.get("ok", False)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def process_update(self, update: Update):
        try:
            logger.info(f"Processing update: {update.update_id}")

            if update.message:
                await self._handle_message(update.message)
            elif update.edited_message:
                await self._handle_edited_message(update.edited_message)
            elif update.callback_query:
                await self._handle_callback_query(update.callback_query)
        except Exception as e:
            logger.error(f"Error processing update: {e}")

    async def _handle_message(self, message):
        chat_id = message.chat.id
        user_name = message.from_.first_name if message.from_ else "Unknown"
        text = message.text or ""

        logger.info(f"Message from {user_name} ({chat_id}): {text}")

        response_text, keyboard_markup = handle_command(text, user_name, chat_id)
        await self.send_message(chat_id, response_text, reply_markup=keyboard_markup)

    async def _handle_edited_message(self, message):
        logger.info(f"Edited message: {message}")

    async def _handle_callback_query(self, callback_query):
        logger.info(f"Callback query: {callback_query}")

        chat_id = callback_query.message.chat.id if callback_query.message else None
        user_name = callback_query.from_.first_name or "Unknown"
        callback_data = callback_query.data or ""

        if not chat_id:
            logger.error("Missing chat_id in callback query")
            return

        response_text, keyboard_markup = handle_command(callback_data, user_name, chat_id)

        await telegram_post(
            f"{self.base_url}/answerCallbackQuery",
            {"callback_query_id": callback_query.id}
        )

        message_id = callback_query.message.message_id if callback_query.message else None
        if message_id:
            edit_data = {
                "chat_id": chat_id,
                "message_id": message_id,
                "text": response_text,
                "parse_mode": "Markdown"
            }

            if keyboard_markup:
                edit_data["reply_markup"] = keyboard_markup

            logger.info(f"Attempting to edit message with data: {edit_data}")

            result = await telegram_post(
                f"{self.base_url}/editMessageText",
                edit_data
            )

            if not result.get("ok"):
                logger.error(f"Edit message failed: {result}")
                await self.send_message(chat_id, response_text, reply_markup=keyboard_markup)
        else:
            await self.send_message(chat_id, response_text, reply_markup=keyboard_markup)
