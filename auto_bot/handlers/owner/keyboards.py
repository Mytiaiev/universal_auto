from telegram import KeyboardButton

from auto_bot.handlers.owner.static_text import *

payments_buttons = [KeyboardButton(f'{TRANSFER_MONEY}'),
                    KeyboardButton(f'{GENERATE_LINK_PORTMONE}')]

data_buttons = [KeyboardButton(f'{THE_DATA_IS_CORRECT}'),
                KeyboardButton(f'{THE_DATA_IS_WRONG}')]

commission_buttons = [KeyboardButton(f'{COMMISSION_ONLY_PORTMONE}'),
                      KeyboardButton(f'{MY_COMMISSION}')]
