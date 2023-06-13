import logging
import sys
import os
import time
import telegram
from telegram import Bot
from telegram.ext import Updater


bot_token = os.environ['TELEGRAM_TOKEN']
webhook_url = f'{os.environ["WEBHOOK_URL"]}/webhook/'
bot = Bot(token=bot_token)
updater = Updater(bot_token, use_context=True)
retry_count = 0
retry_limit = 5
retry_delay = 1.0

while retry_count < retry_limit:
    try:
        bot.setWebhook(url=webhook_url)
        break
    except telegram.error.RetryAfter as e:
        retry_count += 1
        delay = e.retry_after
        print(f"Flood control exceeded. Retrying in {delay} seconds...")
        time.sleep(delay)
    except telegram.TelegramError as e:
        print(f"Failed to set webhook: {e}")
        break

if retry_count >= retry_limit:
    print("Webhook set failed after multiple retries")


# Global variable - the best way I found to init Telegram bot
try:
    pass
except telegram.error.Unauthorized:
    logging.error("Invalid TELEGRAM_TOKEN.")
    sys.exit(1)
