from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from auto_bot.handlers.order.static_text import *
from scripts.conversion import coord_to_link

order_keyboard = [
    KeyboardButton(text=f"\U0001f4b7 {INCREASE_PRICE}"),
    KeyboardButton(text=f"\u23F0 {TODAY}"),
    KeyboardButton(text=f"\u274c {CANCEL}")
]

timeorder_keyboard = [
    [KeyboardButton(text=f"\u2705 {NOW}"),
     KeyboardButton(text=f"\u23F0 {TODAY}")],
    [KeyboardButton(text=f"\u274c {CANCEL}")]
]

share_location = [
    [KeyboardButton(text=f"\U0001F4CD {LOCATION}", request_location=True)]
]

location_keyboard = [
    KeyboardButton(text=f"\u2705 {LOCATION_CORRECT}"),
    KeyboardButton(text=f"\u274c {LOCATION_WRONG}")
]

payment_keyboard = [
    KeyboardButton(text=f"\U0001f4b7 {CASH}"),
    # KeyboardButton(text=f"\U0001f4b8 {PAYCARD}")
]

keyboard_comment_for_client = [
    KeyboardButton(text=f"\u2705 {LOCATION_CORRECT}"),
    KeyboardButton(text=f"\u274c {LOCATION_WRONG}")
]

increase_price_keyboard = [
    KeyboardButton(text=f"\U0001f4b7 50 грн"),
    KeyboardButton(text=f"\U0001f4b7 100 грн"),
    KeyboardButton(text=f"\U0001f4b7 150 грн")
]


def inline_spot_keyboard(end_lat, end_lng):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[8], url=coord_to_link(end_lat, end_lng))]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_markup_accept(pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[1], callback_data=f"Accept_order {pk}")],
        [InlineKeyboardButton(order_inline_buttons[0], callback_data=f"Reject_order {pk}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_client_spot(pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[2], callback_data=f"Сlient_on_site {pk}")]]
    return InlineKeyboardMarkup(keyboard)


def inline_finish_order(end_lat, end_lng, pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[8], url=coord_to_link(end_lat, end_lng))],
        [InlineKeyboardButton(order_inline_buttons[7], callback_data=f"End_trip {pk}")],

    ]
    return InlineKeyboardMarkup(keyboard)


def inline_repeat_keyboard(pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[5], callback_data=f"Accept {pk}")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data=f"End_trip {pk}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_route_keyboard(pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[3], callback_data=f"Along_the_route {pk}")],
        [InlineKeyboardButton(order_inline_buttons[4], callback_data=f"Off_route {pk}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_comment_for_client():
    keyboard = [[
        InlineKeyboardButton(order_inline_buttons[9], callback_data="Comment client")
    ]]
    return InlineKeyboardMarkup(keyboard)


def inline_reject_order(pk=None):
    keyboard = [[
        InlineKeyboardButton(f"\u274c {CANCEL}", callback_data=f"Client_reject {pk}")
    ]]
    return InlineKeyboardMarkup(keyboard)
