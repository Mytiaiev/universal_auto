from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from app.models import Driver
from auto_bot.handlers.driver_manager.static_text import *
from auto_bot.handlers.order.static_text import order_inline_buttons


def inline_driver_paid_kb(pk):
    keyboard = [
        [InlineKeyboardButton(paid_inline_buttons[0], callback_data=f"Paid_driver true {pk}"),
         InlineKeyboardButton(paid_inline_buttons[1], callback_data=f"Paid_driver false {pk}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_earning_report_kb():
    keyboard = [
        [InlineKeyboardButton(report_period[0], callback_data="Weekly_report")],
        [InlineKeyboardButton(report_period[1], callback_data="Daily_report")],
        [InlineKeyboardButton(report_period[2], callback_data="Custom_report")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_efficiency_report_kb():
    keyboard = [
        [InlineKeyboardButton(report_period[1], callback_data="Efficiency_daily")],
        [InlineKeyboardButton(report_period[2], callback_data="Efficiency_custom")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


create_user_keyboard = [KeyboardButton(f'{CREATE_USER}'),
                        KeyboardButton(f'{CREATE_VEHICLE}')]

role_keyboard = [KeyboardButton(text=f"{USER_DRIVER}"),
                 KeyboardButton(text=f"{USER_MANAGER_DRIVER}")]

fleets_keyboard = [[KeyboardButton(F_UBER)],
                   [KeyboardButton(F_UKLON)],
                   [KeyboardButton(F_BOLT)]]
fleet_job_keyboard = [[KeyboardButton(f'- {SEND_JOB}')],
                      [KeyboardButton(f'- {DECLINE_JOB}')]]

drivers_status_buttons = [[KeyboardButton(f'- {Driver.ACTIVE}')],
                          [KeyboardButton(f'- {Driver.WITH_CLIENT}')],
                          [KeyboardButton(f'- {Driver.WAIT_FOR_CLIENT}')],
                          [KeyboardButton(f'- {Driver.OFFLINE}')]
                   ]

