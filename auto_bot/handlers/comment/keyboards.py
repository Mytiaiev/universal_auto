from telegram import KeyboardButton

STAR = '\U00002b50'

comment_keyboard = [
    [KeyboardButton(text=f"{STAR * 5}")],
    [KeyboardButton(text=f"{STAR * 4}")],
    [KeyboardButton(text=f"{STAR * 3}")],
    [KeyboardButton(text=f"{STAR * 2}")],
    [KeyboardButton(text=f"{STAR}")],
]
