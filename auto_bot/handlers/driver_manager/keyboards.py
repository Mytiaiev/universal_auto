from telegram import KeyboardButton

from app.models import Driver
from auto_bot.handlers.driver_manager.static_text import *
SEND_JOB = 'Подати заявку'
DECLINE_JOB = 'Відхилити заявку'
create_user_keyboard = [KeyboardButton(f'{CREATE_USER}'),
                        KeyboardButton(f'{CREATE_VEHICLE}')]

role_keyboard = [KeyboardButton(text=f"{USER_DRIVER}"),
                 KeyboardButton(text=f"{USER_MANAGER_DRIVER}")]

fleets_keyboard = [[KeyboardButton(F_UBER)],
                   [KeyboardButton(F_UKLON)],
                   [KeyboardButton(F_BOLT)]]
fleet_job_keyboard = [[KeyboardButton(f'- {SEND_JOB}')],
                      [KeyboardButton(f'- {DECLINE_JOB}')]]

drivers_status_buttons = [[KeyboardButton(f'- {Driver.ACTIVE}')],
                          [KeyboardButton(f'- {Driver.WITH_CLIENT}')],
                          [KeyboardButton(f'- {Driver.WAIT_FOR_CLIENT}')],
                          [KeyboardButton(f'- {Driver.OFFLINE}')]
                   ]
