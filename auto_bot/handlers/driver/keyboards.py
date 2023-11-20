from datetime import timedelta

from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from auto_bot.handlers.driver.static_text import *
from auto_bot.handlers.main.keyboards import main
from auto_bot.handlers.order.static_text import order_inline_buttons

service_auto_buttons = [KeyboardButton(f'{SERVICEABLE}'), KeyboardButton(f'{BROKEN}')]


def inline_debt_keyboard():
    debt_buttons = [[InlineKeyboardButton(text=f'{SEND_REPORT_DEBT}', callback_data='photo_debt')]]
    return InlineKeyboardMarkup(debt_buttons)


def inline_dates_kb(event, day, back_step):
    dates = []
    start_date = day
    for i in range(7):
        dates.append([InlineKeyboardButton(text=f'{start_date.strftime("%d.%m")}',
                                           callback_data=f'{event} {start_date.strftime("%Y-%m-%d")}')])
        start_date += timedelta(days=1)

    dates.append([InlineKeyboardButton(order_inline_buttons[6], callback_data=back_step)],)
    dates.append(main)

    return InlineKeyboardMarkup(dates)
