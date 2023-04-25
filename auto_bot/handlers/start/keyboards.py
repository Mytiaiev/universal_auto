from telegram import KeyboardButton

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
