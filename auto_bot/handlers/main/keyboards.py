from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from auto_bot.handlers.main.static_text import main_buttons

contact_keyboard = [
    KeyboardButton(text=main_buttons[3], request_contact=True)
]

driver_keyboard = [
    KeyboardButton(text=main_buttons[0]),
    KeyboardButton(text=main_buttons[4]),
    KeyboardButton(text=main_buttons[5])
]


def inline_user_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[0], callback_data=f"Call_taxi")],
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_start_driver_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        [InlineKeyboardButton(main_buttons[4], callback_data="Start_work")],
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_finish_driver_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[5], callback_data="Finish_work")],
    ]
    return InlineKeyboardMarkup(keyboard)


def markup_keyboard(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def markup_keyboard_onetime(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
