from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from auto_bot.handlers.main.static_text import main_buttons, driver_option_buttons

contact_keyboard = [
    KeyboardButton(text=main_buttons[3], request_contact=True)
]

driver_keyboard = [
    KeyboardButton(text=main_buttons[0]),
    KeyboardButton(text=main_buttons[4]),
    KeyboardButton(text=main_buttons[5])
]


def inline_more_func_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[1], callback_data="Comment client")],
        [InlineKeyboardButton(main_buttons[2], callback_data="Job_application")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_driver_func_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        # [InlineKeyboardButton(driver_option_buttons[0], callback_data="Service_car")],
        # [InlineKeyboardButton(driver_option_buttons[1], callback_data="Crash_car")],
        [InlineKeyboardButton(driver_option_buttons[2], callback_data="Off day_driver")],
        [InlineKeyboardButton(driver_option_buttons[3], callback_data="Sick day_driver")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_user_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        [InlineKeyboardButton(main_buttons[6], callback_data="Other_user")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_start_driver_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[4], callback_data="Start_work")],
        [InlineKeyboardButton(main_buttons[6], callback_data="More_driver")]
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
