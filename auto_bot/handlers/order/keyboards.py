from telegram import KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

from auto_bot.handlers.main.static_text import main_buttons
from auto_bot.handlers.order.static_text import *
from scripts.conversion import coord_to_link
from auto_bot.handlers.main.keyboards import main

share_location = [
    [KeyboardButton(text=search_inline_buttons[5], request_location=True)]
]


def personal_order_start_kb():
    keyboard = [
        [InlineKeyboardButton(personal_order_buttons[0], callback_data="Personal_order_info")],
        [InlineKeyboardButton(personal_order_buttons[1], callback_data="Personal_order_terms")],
        [InlineKeyboardButton(personal_order_buttons[2], callback_data="Personal_order")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def personal_order_back_kb():
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Personal_driver")]
    ]
    return InlineKeyboardMarkup(keyboard)


def personal_order_time_kb(pk=None):
    keyboard = [
        [InlineKeyboardButton(pd_time_buttons[0], callback_data=f"{pk} Hour 2"),
         InlineKeyboardButton(pd_time_buttons[1], callback_data=f"{pk} Hour 3")],
        [InlineKeyboardButton(pd_time_buttons[2], callback_data=f"{pk} Hour 4"),
         InlineKeyboardButton(pd_time_buttons[3], callback_data=f"{pk} Hour 5")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Return_info")],
    ]
    if pk:
        keyboard = [
            [InlineKeyboardButton(pd_time_buttons[7], callback_data=f"{pk} Hour 1")],
            [InlineKeyboardButton(pd_time_buttons[0], callback_data=f"{pk} Hour 2")],
            [InlineKeyboardButton(pd_time_buttons[1], callback_data=f"{pk} Hour 3")],
            [InlineKeyboardButton(order_inline_buttons[6], callback_data=f"{pk} Back_step_to_finish")],
        ]
    return InlineKeyboardMarkup(keyboard)


def personal_order_end_kb(pk, pre_finish=None):

    keyboard = [
        [InlineKeyboardButton(pd_time_buttons[4], callback_data=f"Continue_personal {pk}")],
        [InlineKeyboardButton(pd_time_buttons[6], callback_data=f"Finish_personal {pk}")]
    ]
    if pre_finish:
        keyboard.append([InlineKeyboardButton(pd_time_buttons[5], callback_data=f"End_personal {pk}")])
    return InlineKeyboardMarkup(keyboard)


def personal_driver_end_kb(pk):
    keyboard = [
        [InlineKeyboardButton(pd_time_buttons[5], callback_data=f"Finish_personal {pk}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_payment_kb():
    keyboard = [
        [InlineKeyboardButton(price_inline_buttons[4], callback_data="Cash_payment 0")],
        [InlineKeyboardButton(price_inline_buttons[5], callback_data="Card_payment 1")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Return_info")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_second_payment_kb(pk):
    keyboard = [
        [InlineKeyboardButton(price_inline_buttons[4], callback_data=f"Second_cash_payment {pk}")],
        [InlineKeyboardButton(price_inline_buttons[5], callback_data=f"Second_card_payment {pk}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_location_kb():
    keyboard = [
        [InlineKeyboardButton(search_inline_buttons[7], callback_data="Right_place"),
         InlineKeyboardButton(search_inline_buttons[6], callback_data="Wrong_place")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_start_order_kb():
    keyboard = [
        # [InlineKeyboardButton(search_inline_buttons[4], callback_data="Now_order")],
        [InlineKeyboardButton(search_inline_buttons[3], callback_data="On_time_order")],
        [InlineKeyboardButton(main_buttons[10], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_search_kb(pk):
    keyboard = [
        [InlineKeyboardButton(search_inline_buttons[0], callback_data=f"Increase_price {pk}")],
        [InlineKeyboardButton(search_inline_buttons[1], callback_data="Continue_search")],
        [InlineKeyboardButton(search_inline_buttons[3], callback_data="No_driver_time_order")],
        [InlineKeyboardButton(search_inline_buttons[2], callback_data=f"Client_reject {pk}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_increase_price_kb(pk):
    keyboard = [
        [InlineKeyboardButton(price_inline_buttons[0], callback_data="30"),
         InlineKeyboardButton(price_inline_buttons[1], callback_data="50")],
        [InlineKeyboardButton(price_inline_buttons[2], callback_data="100"),
         InlineKeyboardButton(price_inline_buttons[3], callback_data="150")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data=f"Ask_action {pk}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_spot_keyboard(end_lat, end_lng, pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[8], url=coord_to_link(end_lat, end_lng))],
    ]
    if pk:
        keyboard.append([InlineKeyboardButton(order_inline_buttons[0], callback_data=f"Reject_order {pk}")])
    return InlineKeyboardMarkup(keyboard)


def inline_markup_accept(pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[1], callback_data=f"Accept_order {pk}")]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_client_spot(pk=None, message=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[2], callback_data=f"Client_on_site {pk} {message}")]]
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
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[9], callback_data="Comment client")],
        main]
    return InlineKeyboardMarkup(keyboard)


def inline_reject_order(pk=None):
    keyboard = [[
        InlineKeyboardButton(search_inline_buttons[2], callback_data=f"Client_reject {pk}")
    ]]
    return InlineKeyboardMarkup(keyboard)


def inline_time_order_kb(pk=None):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[2], callback_data=f"Start_route {pk}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_choose_date_kb(back_step):
    keyboard = [
        [InlineKeyboardButton(date_inline_buttons[0], callback_data="Today_order")],
        [InlineKeyboardButton(date_inline_buttons[1], callback_data="Tomorrow_order")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data=back_step)]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_add_info_kb(back_step):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[10], callback_data="Add_information")],
        [InlineKeyboardButton(order_inline_buttons[11], callback_data="Choose_payment")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data=back_step)]
    ]
    return InlineKeyboardMarkup(keyboard)


def inline_change_currency_trip(pk):
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[12], callback_data=f"Change_payments {pk}")],
    ]
    return InlineKeyboardMarkup(keyboard)


def user_duty():
    keyboard = [
        [InlineKeyboardButton(order_inline_buttons[13], callback_data="Duty")],
        [InlineKeyboardButton(order_inline_buttons[6], callback_data="Back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)