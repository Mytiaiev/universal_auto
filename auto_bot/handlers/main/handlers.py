import json
import traceback
import html
import os
import rollbar

from django.utils import timezone
from telegram import BotCommand, Update, ParseMode, ReplyKeyboardRemove
from telegram.ext import ConversationHandler

from app.models import User, Client, UseOfCars
from auto_bot.handlers.main.keyboards import markup_keyboard, inline_user_kb, contact_keyboard, get_start_kb, \
    inline_owner_kb, inline_manager_kb, get_more_func_kb, inline_finish_driver_kb, inline_start_driver_kb
import logging

from auto_bot.handlers.main.static_text import share_phone_text, user_greetings_text, help_text, DEVELOPER_CHAT_ID, \
    more_func_text

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)
logger = logging.getLogger(__name__)

processed_files = []


def start(update, context):
    context.user_data.clear()
    menu(update, context)
    chat_id = update.effective_chat.id
    users = User.objects.filter(chat_id=chat_id)
    if not users:
        Client.objects.create(chat_id=chat_id, name=update.message.from_user.first_name,
                              second_name=update.message.from_user.last_name)
        update.message.reply_text(share_phone_text, reply_markup=markup_keyboard([contact_keyboard]))
    elif users and len(users) == 1:
        user = users.first()
        if user.phone_number:
            update.message.reply_text(user_greetings_text, reply_markup=get_start_kb(user))
        else:
            update.message.reply_text(share_phone_text, reply_markup=markup_keyboard([contact_keyboard]))
    else:
        if any(user.role == "OWNER" for user in users):
            reply_markup = inline_owner_kb()
        elif any(user.role == "DRIVER_MANAGER" for user in users):
            reply_markup = inline_manager_kb()
        else:
            user = users.first()
            reply_markup = inline_finish_driver_kb() if UseOfCars.objects.filter(user_vehicle=user,
                                                                                 created_at__date=timezone.now().date(),
                                                                                 end_at=None)\
                else inline_start_driver_kb()
        update.message.reply_text(user_greetings_text, reply_markup=reply_markup)


def start_query(update, context):
    query = update.callback_query
    users = User.objects.filter(chat_id=update.effective_chat.id)
    if len(users) == 1:
        user = users.first()
        reply_markup = get_start_kb(user)
    else:
        if any(user.role == "OWNER" for user in users):
            reply_markup = inline_owner_kb()
        elif any(user.role == "DRIVER_MANAGER" for user in users):
            reply_markup = inline_manager_kb()
        else:
            user = users.first()
            reply_markup = inline_finish_driver_kb() if UseOfCars.objects.filter(user_vehicle=user,
                                                                                 created_at__date=timezone.now().date(),
                                                                                 end_at=None) \
                else inline_start_driver_kb()
    query.edit_message_text(text=user_greetings_text)
    query.edit_message_reply_markup(reply_markup=reply_markup)


def more_function(update, context):
    query = update.callback_query
    query.edit_message_text(text=more_func_text)
    query.edit_message_reply_markup(reply_markup=get_more_func_kb(query.data))


def update_phone_number(update, context):
    chat_id = update.message.chat.id
    user = Client.get_by_chat_id(chat_id)
    phone_number = update.message.contact.phone_number
    if phone_number and user:
        if len(phone_number) == 12:
            phone_number = f'+{phone_number}'
        user.phone_number = phone_number
        user.save()
        update.message.reply_text('Дякуємо ми отримали ваш номер телефону',
                                  reply_markup=ReplyKeyboardRemove())
    context.bot.send_message(chat_id=chat_id, text=user_greetings_text, reply_markup=inline_user_kb())


def helptext(update, context):
    update.message.reply_text(help_text)


# Getting id for users
def get_id(update, context):
    chat_id = update.message.chat.id
    update.message.reply_text(f"Ваш id: {chat_id}")


def cancel(update, context):
    context.user_data.clear()
    return ConversationHandler.END


rollbar.init(access_token=os.environ.get('ROLLBAR_TOKEN'),
             environment=os.environ.get('ROLLBAR_ENV'),
             code_version='1.0')


def error_handler(update, context) -> None:
    """Log the error and send a rollbar message to notify the developer."""
    if not os.environ.get('DEBUG'):
        rollbar.report_exc_info()
    else:
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
    # chat_id = update.effective_chat.id
    # driver_manager = DriverManager.get_by_chat_id(chat_id)
    # driver = Driver.get_by_chat_id(chat_id)
    # manager = ServiceStationManager.get_by_chat_id(chat_id)
    # owner = Owner.get_by_chat_id(chat_id)
    standart_commands = [
        BotCommand("/start", "Запустити бот"),
    ]
    # if driver is not None:
    #     standart_commands.extend([
    #         BotCommand("/status", "Змінити статус водія"),
    #         BotCommand("/status_car", "Змінити статус автомобіля"),
    #         BotCommand("/sending_report", "Відправити звіт про оплату заборгованості"),
    #         BotCommand("/option", "Взяти вихідний/лікарняний/Сповістити про пошкодження/Записатись до СТО")])
    # elif driver_manager is not None:
    #     standart_commands.extend([
    #         BotCommand("/car_status", "Показати всі зломлені машини"),
    #         BotCommand("/driver_status", "Показати водіїв за їх статусом"),
    #         BotCommand("/add", "Створити користувачів та автомобілі"),
    #         BotCommand("/add_imei_gps_to_driver", "Додати авто gps_imei"),
    #         BotCommand("/add_vehicle_to_driver", "Додати водію автомобіль"),
    #         BotCommand("/add_job_application_to_fleets", "Додати водія в автопарк")])
    # elif manager is not None:
    #     standart_commands.extend([
    #         BotCommand("/send_report", "Відправити звіт про ремонт")])
    # elif owner is not None:
    #     standart_commands.extend([
    #         BotCommand("/report", "Загрузити та побачити недільні звіти"),
    #         BotCommand("/rating", "Побачити рейтинг водіїв по автопарках за тиждень"),
    #         BotCommand("/total_weekly_rating", "Побачити рейтинг водіїв загальну за тиждень"),
    #         BotCommand("/payment", "Перевести кошти або сгенерити лінк на оплату"),
    #         BotCommand("/download_report", "Загрузити тижневі звіти")])

    context.bot.set_my_commands(standart_commands)
