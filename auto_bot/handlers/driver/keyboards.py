from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from auto_bot.handlers.driver.static_text import *

service_auto_buttons = [KeyboardButton(f'{SERVICEABLE}'), KeyboardButton(f'{BROKEN}')]


def inline_debt_keyboard():
    debt_buttons = [[InlineKeyboardButton(text=f'{SEND_REPORT_DEBT}', callback_data='photo_debt')]]
    return InlineKeyboardMarkup(debt_buttons)
