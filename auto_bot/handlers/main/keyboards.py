from telegram import KeyboardButton, ReplyKeyboardMarkup

start_keyboard = [
    KeyboardButton(text="\U0001f696 Викликати Таксі"),
    KeyboardButton(text="\U0001f4e2 Залишити відгук"),
    KeyboardButton(text="\U0001F4E8 Залишити заявку на роботу"),
    KeyboardButton(text="\U0001f4f2 Надати номер телефону", request_contact=True)
]

driver_keyboard = [
    KeyboardButton(text="\U0001f696 Викликати Таксі"),
    KeyboardButton(text="\U0001F4B0 Розпочати роботу")
]


def markup_keyboard(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def markup_keyboard_onetime(keyboard):
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)