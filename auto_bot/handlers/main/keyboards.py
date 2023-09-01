from django.utils import timezone
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from app.models import UseOfCars, ParkSettings
from auto_bot.handlers.main.static_text import main_buttons, driver_option_buttons, manager_main_buttons, about_us
from auto_bot.handlers.order.static_text import order_inline_buttons

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
        [InlineKeyboardButton(main_buttons[2], callback_data="Job_application")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_driver_func_kb():
    keyboard = [
        # [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        # [InlineKeyboardButton(driver_option_buttons[0], callback_data="Service_car")],
        # [InlineKeyboardButton(driver_option_buttons[1], callback_data="Crash_car")],
        [InlineKeyboardButton(driver_option_buttons[2], callback_data="Off day_driver")],
        [InlineKeyboardButton(driver_option_buttons[3], callback_data="Sick day_driver")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_user_kb():
    keyboard = [
        # [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        [InlineKeyboardButton(main_buttons[0], callback_data="On_time_order")],
        [InlineKeyboardButton(main_buttons[9], url=ParkSettings.get_value('SHIPPING_CHILDS'))],
        [InlineKeyboardButton(main_buttons[6], callback_data="Other_user")],
        [InlineKeyboardButton(main_buttons[7], callback_data="About_us")],
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_about_us(url1, url2):
    keyboard = [
        [InlineKeyboardButton(about_us[0], url=url1)],
        [InlineKeyboardButton(about_us[1], url=url2)],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_manager_kb():
    keyboard = [
        [InlineKeyboardButton(manager_main_buttons[0], callback_data="Setup_drivers")],
        [InlineKeyboardButton(manager_main_buttons[2], callback_data="Setup_vehicles")],
        [InlineKeyboardButton(manager_main_buttons[1], callback_data="Get_statistic")],
        [InlineKeyboardButton(main_buttons[6], callback_data="Other_manager")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_more_manager_kb():
    keyboard = [
        # [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        [InlineKeyboardButton(main_buttons[0], callback_data="On_time_order")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_owner_kb():
    keyboard = [
        # [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        [InlineKeyboardButton(main_buttons[0], callback_data="On_time_order")],
        [InlineKeyboardButton(manager_main_buttons[0], callback_data="Update_drivers")],
        [InlineKeyboardButton(manager_main_buttons[1], callback_data="Get_report")],
        [InlineKeyboardButton(main_buttons[6], callback_data="Other_manager")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_start_driver_kb():
    keyboard = [
        # [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        [InlineKeyboardButton(main_buttons[0], callback_data="On_time_order")],
        [InlineKeyboardButton(main_buttons[6], callback_data="More_driver")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_work_driver_kb():
    keyboard = [
        [InlineKeyboardButton(driver_option_buttons[2], callback_data="Off day_driver")],
        [InlineKeyboardButton(driver_option_buttons[3], callback_data="Sick day_driver")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_start_kb(user):
    role_reply_markup = {
        "DRIVER": inline_start_driver_kb(),
        "CLIENT": inline_user_kb(),
        "DRIVER_MANAGER": inline_manager_kb(),
        "OWNER": inline_owner_kb()
    }
    reply_markup = role_reply_markup.get(user.role, inline_user_kb())
    return reply_markup


def get_more_func_kb(data):
    other_func = {
        "More_driver": inline_driver_func_kb(),
        "Other_user": inline_more_func_kb(),
        "Other_manager": inline_more_manager_kb()
    }
    reply_markup = other_func.get(data)
    return reply_markup


def markup_keyboard(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def markup_keyboard_onetime(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


main = [InlineKeyboardButton(main_buttons[8], callback_data="Back_to_main")]


def back_to_main_menu():
    return InlineKeyboardMarkup([main])
