from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from auto_bot.handlers.order.static_text import *


order_keyboard = [
    KeyboardButton(text=f"\u2705 {CONTINUE}"),
    KeyboardButton(text=f"\u274c {CANCEL}")
]

timeorder_keyboard = [
    [KeyboardButton(text="Замовити на зараз", request_location=True),
     KeyboardButton(text=f"{TODAY}")],
    [KeyboardButton(text=f"\u274c {CANCEL}")]
]

location_keyboard = [
    KeyboardButton(text=f"\u2705 {LOCATION_CORRECT}"),
    KeyboardButton(text=f"\u274c {LOCATION_WRONG}")
]

payment_keyboard = [
    KeyboardButton(text=f"\U0001f4b7 {CASH}"),
    # KeyboardButton(text=f"\U0001f4b8 {PAYCARD}")
]


def inline_spot_keyboard(pk=None):
    keyboard = [
                    [InlineKeyboardButton("\u2705 Машина вже на місці", callback_data=f"On_the_spot {pk}")],
                    [InlineKeyboardButton("\u274c Відхилити", callback_data=f"Reject_order {pk}")],
                    ]
    return InlineKeyboardMarkup(keyboard)


def inline_markup_accept(pk=None):
    keyboard = [
        [InlineKeyboardButton("\u2705 Прийняти замовлення", callback_data=f"Accept_order {pk}")],
        [InlineKeyboardButton("\u274c Відхилити", callback_data=f"Reject_order {pk}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_client_spot(pk=None):
    keyboard = [[InlineKeyboardButton("\u2705 Клієнт на місці", callback_data=f"Сlient_on_site {pk}")]]
    return InlineKeyboardMarkup(keyboard)


def inline_route_keyboard(pk=None):
    keyboard = [
        [InlineKeyboardButton("\u2705 Рухались по маршруту", callback_data=f"Along_the_route {pk}")],
        [InlineKeyboardButton("\u274c Відхилялись від маршрута", callback_data=f"Off_route {pk}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_finish_order(pk=None):
    keyboard = [[
        InlineKeyboardButton("Завершити поїздку", callback_data=f"End_trip {pk}")
    ]]
    return InlineKeyboardMarkup(keyboard)


def inline_reject_order(pk=None):
    keyboard = [[
        InlineKeyboardButton("\u274c Відмовитись від замовлення", callback_data=f"Client_order_reject {pk}")
    ]]
    return InlineKeyboardMarkup(keyboard)