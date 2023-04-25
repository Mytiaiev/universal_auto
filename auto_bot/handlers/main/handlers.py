import json
import traceback
import html
from telegram import BotCommand, ReplyKeyboardMarkup, Update, ParseMode

from app.models import User, Driver, DriverManager, Owner, ServiceStationManager
from auto_bot.handlers.main.keyboards import driver_keyboard, start_keyboard, markup_keyboard
import logging

from auto_bot.handlers.main.static_text import share_phone_text, user_greetings_text, driver_greetings_text, help_text, \
    DEVELOPER_CHAT_ID

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

processed_files = []


def start(update, context):
    context.user_data.clear()
    menu(update, context)
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    if user:
        if user.phone_number:
            if Driver.get_by_chat_id(chat_id):
                update.message.reply_text(driver_greetings_text, reply_markup=markup_keyboard(driver_keyboard))
            else:
                update.message.reply_text(user_greetings_text)
                user.chat_id = chat_id
                user.save()
                update.message.reply_text('Зробіть вибір', reply_markup=markup_keyboard(start_keyboard[:3]))
        else:
            update.message.reply_text(share_phone_text,
                                      reply_markup=markup_keyboard(start_keyboard[3:]))
    else:
        User.objects.create(
            chat_id=chat_id,
            name=update.message.from_user.first_name,
            second_name=update.message.from_user.last_name
        )
        update.message.reply_text(share_phone_text,
                                  reply_markup=markup_keyboard(start_keyboard[3:]))


def update_phone_number(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    phone_number = update.message.contact.phone_number
    if (phone_number and user):
        if len(phone_number) == 12:
            phone_number = f'+{phone_number}'
        user.phone_number = phone_number
        user.chat_id = chat_id
        user.save()
        update.message.reply_text('Дякуємо ми отримали ваш номер телефону',
                                  reply_markup=markup_keyboard(start_keyboard[:3]))


def helptext(update, context) -> str:
    update.message.reply_text(help_text)


# Getting id for users
def get_id(update, context):
    chat_id = update.message.chat.id
    update.message.reply_text(f"Ваш id: {chat_id}")


def cancel(update, context):
    context.user_data.clear()


def error_handler(update, context) -> None:
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f'An exception was raised while handling an update\n'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
        f'<pre>{html.escape(tb_string)}</pre>'
    )

    # Finally, send the message
    context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=message, parse_mode=ParseMode.HTML)


def menu(update, context):
    chat_id = update.message.chat.id
    driver_manager = DriverManager.get_by_chat_id(chat_id)
    driver = Driver.get_by_chat_id(chat_id)
    manager = ServiceStationManager.get_by_chat_id(chat_id)
    owner = Owner.get_by_chat_id(chat_id)
    standart_commands = [
        BotCommand("/start", "Щоб зареєструватись та замовити таксі"),
        BotCommand("/help", "Допомога"),
        BotCommand("/id", "Дізнатись id"),
    ]
    if driver is not None:
        standart_commands.extend([
            BotCommand("/status", "Змінити статус водія"),
            BotCommand("/car_change", "Реєстрація робочого автомобіля на сьогодні"),
            BotCommand("/status_car", "Змінити статус автомобіля"),
            BotCommand("/sending_report", "Відправити звіт про оплату заборгованості"),
            BotCommand("/option", "Взяти вихідний/лікарняний/Сповістити про пошкодження/Записатись до СТО")])
    elif driver_manager is not None:
        standart_commands.extend([
            BotCommand("/car_status", "Показати всі зломлені машини"),
            BotCommand("/driver_status", "Показати водіїв за їх статусом"),
            BotCommand("/add", "Створити користувачів та автомобілі"),
            BotCommand("/add_imei_gps_to_driver", "Додати авто gps_imei"),
            BotCommand("/add_vehicle_to_driver", "Додати водію автомобіль"),
            BotCommand("/add_job_application_to_fleets", "Додати водія в автопарк")])
    elif manager is not None:
        standart_commands.extend([
            BotCommand("/send_report", "Відправити звіт про ремонт")])
    elif owner is not None:
        standart_commands.extend([
            BotCommand("/report", "Загрузити та побачити недільні звіти"),
            BotCommand("/rating", "Побачити рейтинг водіїв по автопарках за тиждень"),
            BotCommand("/total_weekly_rating", "Побачити рейтинг водіїв загальну за тиждень"),
            BotCommand("/payment", "Перевести кошти або сгенерити лінк на оплату"),
            BotCommand("/download_report", "Загрузити тижневі звіти") ])

    context.bot.set_my_commands(standart_commands)