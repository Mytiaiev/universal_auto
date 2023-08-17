from datetime import datetime, timedelta
from django.utils import timezone
from telegram import ReplyKeyboardRemove, InlineKeyboardMarkup
from telegram.ext import ConversationHandler

from app.models import Driver, Vehicle, Report_of_driver_debt, Event
from auto_bot.handlers.driver.keyboards import service_auto_buttons, inline_debt_keyboard, inline_dates_kb
from auto_bot.handlers.driver.static_text import *
from auto_bot.handlers.main.keyboards import markup_keyboard_onetime


def status_car(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:

        context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть статус автомобіля',
                                 reply_markup=markup_keyboard_onetime([service_auto_buttons]))
    else:
        update.message.reply_text(not_driver_text, reply_markup=ReplyKeyboardRemove())


def numberplate(update, context):
    context.user_data['status'] = update.message.text
    update.message.reply_text('Введіть номер автомобіля', reply_markup=ReplyKeyboardRemove())
    context.user_data['driver_state'] = NUMBERPLATE


def change_status_car(update, context):
    context.user_data['licence_place'] = update.message.text.upper()
    number_car = context.user_data['licence_place']
    numberplates = [i.licence_plate for i in Vehicle.objects.all()]
    if number_car in numberplates:
        vehicle = Vehicle.objects.get(licence_plate=number_car)
        vehicle.car_status = context.user_data['status']
        vehicle.save()
        numberplates.clear()
        update.message.reply_text('Статус авто був змінений')
    else:
        update.message.reply_text(
            'Цього номера немає в базі даних або надіслано неправильні дані.'
            ' Зверніться до менеджера або повторіть команду')
    context.user_data['driver_state'] = None


# Sending report for drivers(payment debt)
def sending_report(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:
        context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть опцію:',
                                 reply_markup=inline_debt_keyboard())
        return "WAIT_FOR_DEBT_OPTION"
    else:
        update.message.reply_text(not_driver_text, reply_markup=ReplyKeyboardRemove())


def get_debt_photo(update, context):
    empty_keyboard = InlineKeyboardMarkup([])
    update.callback_query.answer()
    update.callback_query.edit_message_text(text='Надішліть фото оплати заборгованості', reply_markup=empty_keyboard)
    return 'WAIT_FOR_DEBT_PHOTO'


def save_debt_report(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'{image.file_unique_id}.jpg'
        image.download(filename)
        Report_of_driver_debt.objects.create(
            driver=driver,
            image=f'static/{filename}'
        )
        update.message.reply_text(text='Ваш звіт збережено')
        return ConversationHandler.END
    else:
        update.message.reply_text('Будь ласка, надішліть фото', reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_DEBT_PHOTO'


def choose_day_off_or_sick(update, context):
    query = update.callback_query
    data = query.data.split()[0]
    if data == "Off":
        day = timezone.localtime() + timedelta(days=2)
    else:
        day = timezone.localtime()
    query.edit_message_text(select_off_text)
    query.edit_message_reply_markup(inline_dates_kb(data, day))


def take_a_day_off_or_sick_leave(update, context):
    query = update.callback_query
    event_str, date_str = query.data.split()
    event = Event.DAY_OFF if event_str == "Off" else Event.SICK_DAY
    driver = Driver.get_by_chat_id(update.effective_chat.id)
    selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    result = f"Водій {driver} взяв {event} на {selected_date}"
    Event.objects.create(
        full_name_driver=driver,
        event=event,
        event_date=selected_date,
        chat_id=driver.chat_id)
    query.edit_message_text(text=f'Ви взяли {event} на {selected_date}.')
    context.bot.send_message(chat_id=driver.manager.chat_id, text=result)
