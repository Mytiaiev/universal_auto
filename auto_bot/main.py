import os
import time
import telegram
from telegram import Bot
from telegram.ext import Updater


from scripts.redis_conn import redis_instance

bot_token = os.environ['TELEGRAM_TOKEN']
webhook_url = f'{os.environ["WEBHOOK_URL"]}/webhook/'
bot = Bot(token=bot_token)


def setup_webhook():
    retry_count = 0
    retry_limit = 5

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


distributed_lock = redis_instance.lock('bot_setup_lock', blocking_timeout=10)
if distributed_lock.acquire(blocking=True):
    try:
        setup_webhook()
    finally:
        distributed_lock.release()
