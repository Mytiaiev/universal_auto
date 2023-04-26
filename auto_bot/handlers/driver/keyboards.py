from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from auto_bot.handlers.driver.static_text import *

service_auto_buttons = [KeyboardButton(f'{SERVICEABLE}'), KeyboardButton(f'{BROKEN}')]

option_keyboard = [
    KeyboardButton(text=f"{SIGN_UP_FOR_A_SERVICE_CENTER}"),
    KeyboardButton(text=f"{REPORT_CAR_DAMAGE}"),
    KeyboardButton(text=f"{TAKE_A_DAY_OFF}"),
    KeyboardButton(text=f"{TAKE_SICK_LEAVE}")]


def inline_debt_keyboard():
    debt_buttons = [[InlineKeyboardButton(text=f'{SEND_REPORT_DEBT}', callback_data='photo_debt')]]
    return InlineKeyboardMarkup(debt_buttons)
