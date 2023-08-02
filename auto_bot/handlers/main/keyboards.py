from django.utils import timezone
from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup

from app.models import UseOfCars
from auto_bot.handlers.main.static_text import main_buttons, driver_option_buttons, manager_main_buttons
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
        [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        # [InlineKeyboardButton(driver_option_buttons[0], callback_data="Service_car")],
        # [InlineKeyboardButton(driver_option_buttons[1], callback_data="Crash_car")],
        [InlineKeyboardButton(driver_option_buttons[2], callback_data="Off day_driver")],
        [InlineKeyboardButton(driver_option_buttons[3], callback_data="Sick day_driver")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_user_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        [InlineKeyboardButton(main_buttons[6], callback_data="Other_user")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_manager_kb():
    keyboard = [
        [InlineKeyboardButton(manager_main_buttons[0], callback_data="Update_drivers")],
        [InlineKeyboardButton(manager_main_buttons[1], callback_data="Get_report")],
        [InlineKeyboardButton(manager_main_buttons[2], callback_data="Get_efficiency_report")],
        [InlineKeyboardButton(manager_main_buttons[3], callback_data="Pin_vehicle_to_driver")],
        [InlineKeyboardButton(main_buttons[6], callback_data="Other_manager")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_more_manager_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_owner_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[0], callback_data="Call_taxi")],
        [InlineKeyboardButton(manager_main_buttons[0], callback_data="Update_drivers")],
        [InlineKeyboardButton(manager_main_buttons[1], callback_data="Get_report")],
        [InlineKeyboardButton(main_buttons[6], callback_data="Other_manager")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_start_driver_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[4], callback_data="Start_work")],
        [InlineKeyboardButton(main_buttons[6], callback_data="More_driver")]
    ]
    return InlineKeyboardMarkup(keyboard)


def spam_driver_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[4], callback_data="Start_work")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_finish_driver_kb():
    keyboard = [
        [InlineKeyboardButton(main_buttons[5], callback_data="Finish_work")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_start_kb(user):
    role_reply_markup = {
        "DRIVER": inline_finish_driver_kb() if UseOfCars.objects.filter(user_vehicle=user,
                                                                        created_at__date=timezone.now().date(),
                                                                        end_at=None) else inline_start_driver_kb(),
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
