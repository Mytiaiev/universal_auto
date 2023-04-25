from telegram import KeyboardButton, InlineKeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup

from auto_bot.handlers.order.static_text import *


def markup_keyboard(keyboard):
    return ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True)


def markup_keyboard_onetime(keyboard):
    return ReplyKeyboardMarkup(keyboard=[keyboard], resize_keyboard=True, one_time_keyboard=True)


order_keyboard = [
    KeyboardButton(text=f"\u2705 {CONTINUE}"),
    KeyboardButton(text=f"\u274c {CANCEL}")
]

timeorder_keyboard = [
    KeyboardButton(text="Замовити на зараз", request_location=True),
    KeyboardButton(text=f"{TODAY}")
]

location_keyboard = [
    KeyboardButton(text=f"\u2705 {LOCATION_CORRECT}"),
    KeyboardButton(text=f"\u274c {LOCATION_WRONG}")
]

payment_keyboard = [
    KeyboardButton(text=f"\U0001f4b7 {CASH}"),
    KeyboardButton(text=f"\U0001f4b8 {PAYCARD}")
]


def inline_spot_keyboard(pk=None):
    keyboard = [
                    [InlineKeyboardButton("\u2705 Машина вже на місці", callback_data="On_the_spot")],
                    [InlineKeyboardButton("\u274c Відхилити", callback_data=f"Reject_order {pk}")],
                    ]
    return InlineKeyboardMarkup(keyboard)


def inline_markup_accept(pk=None):
    keyboard = [
        [InlineKeyboardButton("\u2705 Прийняти замовлення", callback_data=f"Accept_order {pk}")],
        [InlineKeyboardButton("\u274c Відхилити", callback_data=f"Reject_order {pk}")],
    ]
    return InlineKeyboardMarkup(keyboard)