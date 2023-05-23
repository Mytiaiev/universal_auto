from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from auto_bot.handlers.order.static_text import *
from scripts.conversion import coord_to_link

share_location = [
    [KeyboardButton(text=search_inline_buttons[5], request_location=True)]
]

location_keyboard = [
    KeyboardButton(text=search_inline_buttons[7]),
    KeyboardButton(text=search_inline_buttons[6])
]

payment_keyboard = [
    KeyboardButton(text=f"\U0001f4b7 {CASH}"),
    # KeyboardButton(text=f"\U0001f4b8 {PAYCARD}")
]


def inline_start_order_kb():
    keyboard = [
        [InlineKeyboardButton(search_inline_buttons[4], callback_data="Now_order")],
        [InlineKeyboardButton(search_inline_buttons[3], callback_data="On_time_order")],
        [InlineKeyboardButton(search_inline_buttons[2], callback_data="Cancel_no_comment")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_search_kb():
    keyboard = [
        [InlineKeyboardButton(search_inline_buttons[0], callback_data="Increase_price")],
        [InlineKeyboardButton(search_inline_buttons[1], callback_data="Continue_search")],
        [InlineKeyboardButton(search_inline_buttons[2], callback_data="Cancel_order")],
        [InlineKeyboardButton(search_inline_buttons[3], callback_data="On_time_order")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_increase_price_kb():
    keyboard = [
        [InlineKeyboardButton(price_inline_buttons[0], callback_data="30"),
         InlineKeyboardButton(price_inline_buttons[1], callback_data="50")],
        [InlineKeyboardButton(price_inline_buttons[2], callback_data="100"),
         InlineKeyboardButton(price_inline_buttons[3], callback_data="150")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_spot_keyboard(end_lat, end_lng, pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[8], url=coord_to_link(end_lat, end_lng))],
        [InlineKeyboardButton(order_inline_buttons[0], callback_data=f"Reject_order {pk}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_markup_accept(pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[1], callback_data=f"Accept_order {pk}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_client_spot(pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[2], callback_data=f"Client_on_site {pk}")]]
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


def inline_time_order_kb(pk=None):
    keyboard = [
        [InlineKeyboardButton(timeorder_inline_buttons[0], callback_data=f"Start_route {pk}")],
    ]
    return InlineKeyboardMarkup(keyboard)
