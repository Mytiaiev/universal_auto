import logging
import sys
import os
import telegram
from telegram import Bot
from telegram.ext import Updater


bot = Bot(token=os.environ['TELEGRAM_TOKEN'])
updater = Updater(os.environ['TELEGRAM_TOKEN'], use_context=True)
# Global variable - the best way I found to init Telegram bot
try:
    pass
except telegram.error.Unauthorized:
    logging.error("Invalid TELEGRAM_TOKEN.")
    sys.exit(1)