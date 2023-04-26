from telegram import KeyboardButton

from app.models import Driver
from auto_bot.handlers.status.static_text import CORRECT_AUTO, NOT_CORRECT_AUTO

status_buttons = [
    KeyboardButton(Driver.ACTIVE),
    KeyboardButton(Driver.WITH_CLIENT),
    KeyboardButton(Driver.WAIT_FOR_CLIENT),
    KeyboardButton(Driver.OFFLINE),
    KeyboardButton(Driver.RENT)]

choose_auto_keyboard = [KeyboardButton(f'{CORRECT_AUTO}'), KeyboardButton(f'{NOT_CORRECT_AUTO}')]
