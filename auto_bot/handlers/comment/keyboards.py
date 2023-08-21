from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from auto_bot.handlers.comment.static_text import STAR


def inline_comment_kb():
    keyboard = [
        [InlineKeyboardButton(STAR * 1, callback_data="1_Star")],
        [InlineKeyboardButton(STAR * 2, callback_data="2_Star")],
        [InlineKeyboardButton(STAR * 3, callback_data="3_Star")],
        [InlineKeyboardButton(STAR * 4, callback_data="4_Star")],
        [InlineKeyboardButton(STAR * 5, callback_data="5_Star")]
    ]
    return InlineKeyboardMarkup(keyboard)
