from telegram import BotCommand, ReplyKeyboardMarkup

from app.models import User, Driver, DriverManager, Owner, ServiceStationManager
from auto_bot.handlers.start.keyboards import driver_keyboard, start_keyboard


def start(update, context):
    context.user_data.clear()
    menu(update, context)
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    if user:
        if user.phone_number:
            if Driver.get_by_chat_id(chat_id):
                reply_markup = ReplyKeyboardMarkup(
                    keyboard=[driver_keyboard],
                    resize_keyboard=True,
                )
                update.message.reply_text('Вітаю! Попрацюємо?)', reply_markup=reply_markup)
            else:
                update.message.reply_text('Привіт! Тебе вітає Універсальне таксі - викликай кнопкою нижче.')
                user.chat_id = chat_id
                user.save()
                reply_markup = ReplyKeyboardMarkup(
                        keyboard=[start_keyboard[:3]],
                        resize_keyboard=True,
                    )
                update.message.reply_text('Зробіть вибір', reply_markup=reply_markup)
        else:
            reply_markup = ReplyKeyboardMarkup(
                keyboard=[start_keyboard[3:]],
                resize_keyboard=True, )
            update.message.reply_text("Будь ласка розшарьте номер телефону для роботи з нашим ботом",
                                      reply_markup=reply_markup)
    else:
        User.objects.create(
            chat_id=chat_id,
            name=update.message.from_user.first_name,
            second_name=update.message.from_user.last_name
        )
        reply_markup = ReplyKeyboardMarkup(
          keyboard=[start_keyboard[3:]],
          resize_keyboard=True,)
        update.message.reply_text("Будь ласка розшарьте номер телефону для роботи з нашим ботом", reply_markup=reply_markup)


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
                                  reply_markup=ReplyKeyboardMarkup(keyboard=[start_keyboard[:3]], resize_keyboard=True))


def helptext(update, context) -> str:
    update.message.reply_text('Для першого кроку зробіть реєстрацію або авторизуйтеся командою /start')


# Getting id for users
def get_id(update, context):
    chat_id = update.message.chat.id
    update.message.reply_text(f"Ваш id: {chat_id}")


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