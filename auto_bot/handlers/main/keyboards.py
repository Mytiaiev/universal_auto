from telegram import KeyboardButton, ReplyKeyboardMarkup
from auto_bot.handlers.main.static_text import main_buttons

start_keyboard = [
    KeyboardButton(text=main_buttons[0]),
    # KeyboardButton(text=main_buttons[2]),
    KeyboardButton(text=main_buttons[3], request_contact=True)
]

driver_keyboard = [
    KeyboardButton(text=main_buttons[0]),
    KeyboardButton(text=main_buttons[4]),
    KeyboardButton(text=main_buttons[5])
]


def markup_keyboard(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def markup_keyboard_onetime(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
