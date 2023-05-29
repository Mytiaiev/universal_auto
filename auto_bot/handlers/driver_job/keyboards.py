from telegram import InlineKeyboardMarkup, InlineKeyboardButton

from auto_bot.handlers.driver_job.static_text import driver_job_name, upload_text


def inline_job_name_kb():
    buttons = [[InlineKeyboardButton(text=driver_job_name, callback_data='Job_driver')]]
    return InlineKeyboardMarkup(buttons)


def inline_ask_docs_kb():
    buttons = [[InlineKeyboardButton(text=upload_text, callback_data='job_photo')]]
    return InlineKeyboardMarkup(buttons)


def inline_ask_auto_kb():
    buttons = [[InlineKeyboardButton(text='Так', callback_data='have_auto')],
               [InlineKeyboardButton(text='Ні', callback_data='no_auto')]]
    return InlineKeyboardMarkup(buttons)
