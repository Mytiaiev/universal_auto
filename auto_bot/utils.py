from auto_bot.main import bot


def send_long_message(chat_id, message, keyboard=None):
    num_parts = (len(message) - 1) // 4096 + 1
    message_parts = [message[i:i + 4096] for i in range(0, len(message), 4096)]
    for i, part in enumerate(message_parts):
        message = bot.send_message(chat_id=chat_id, text=f"{i + 1}/{num_parts}:\n{part}")
    bot.edit_message_reply_markup(chat_id=chat_id, message_id=message.id, reply_markup=keyboard)
