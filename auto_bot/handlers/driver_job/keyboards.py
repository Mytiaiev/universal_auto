from telegram import KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from auto_bot.handlers.driver_job.static_text import JOB_DRIVER

job_name_buttons = [[KeyboardButton(f'{JOB_DRIVER}')]]


def inline_ask_auto_kb():
    buttons = [[InlineKeyboardButton(text='Так', callback_data='have_auto')],
               [InlineKeyboardButton(text='Ні', callback_data='no_auto')]]
    return InlineKeyboardMarkup(buttons)
