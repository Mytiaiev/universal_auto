import time

from app.models import RepairReport, Vehicle, ServiceStationManager
from auto_bot.handlers.service_manager.static_text import *


# Sending report on repair
def numberplate_car(update, context):

    chat_id = update.message.chat.id
    service_station_manager = ServiceStationManager.get_by_chat_id(chat_id)
    if service_station_manager is not None:
        context.user_data['state_ssm'] = LICENCE_PLATE
        update.message.reply_text('Будь ласка, введіть номерний знак автомобіля')
    else:
        update.message.reply_text('Зареєструйтесь як менеджер сервісного центру')


def photo(update, context):
    context.user_data['licence_plate'] = update.message.text.upper()
    numberplates = [i.licence_plate for i in Vehicle.objects.all()]
    if context.user_data['licence_plate'] not in numberplates:
        update.message.reply_text('Написаного вами номера немає в базі, зверніться до менеджера парку')
    context.user_data['state_ssm'] = PHOTO
    update.message.reply_text('Будь ласка, надішліть мені фото звіту про ремонт (Одне фото)')


def start_of_repair(update, context):
    context.user_data['photo'] = update.message.photo[-1].get_file()
    update.message.reply_text('Будь ласка, введіть дату та час початку ремонту у форматі: %Y-%m-%d %H:%M:%S')
    context.user_data['state_ssm'] = START_OF_REPAIR


def end_of_repair(update, context):
    context.user_data['start_of_repair'] = update.message.text + "+00"
    try:
        time.strptime(context.user_data['start_of_repair'], "%Y-%m-%d %H:%M:%S+00")
    except ValueError:
        update.message.reply_text('Недійсна дата')
    context.user_data['state_ssm'] = END_OF_REPAIR
    update.message.reply_text("Будь ласка, введіть дату та час закінчення ремонту у форматі: %Y-%m-%d %H:%M:%S")


def send_report_to_db_and_driver(update, context):
    context.user_data['end_of_repair'] = update.message.text + '+00'
    try:
        time.strptime(context.user_data['end_of_repair'], "%Y-%m-%d %H:%M:%S+00")
    except ValueError:
        update.message.reply_text('Недійсна дата')

    repair = RepairReport(
                    repair=context.user_data['photo']["file_path"],
                    numberplate=context.user_data['licence_plate'],
                    start_of_repair=context.user_data['start_of_repair'],
                    end_of_repair=context.user_data['end_of_repair'])
    repair.save()
    context.user_data['state_ssm'] = None
    update.message.reply_text('Ваш звіт збережено в базі даних')