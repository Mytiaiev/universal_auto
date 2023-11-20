from django.utils import timezone
from telegram import ReplyKeyboardRemove
from app.models import Vehicle, Driver, UseOfCars
from auto_bot.handlers.driver.static_text import V_ID
from auto_bot.handlers.main.keyboards import markup_keyboard_onetime, markup_keyboard
from auto_bot.handlers.status.keyboards import choose_auto_keyboard, correct_keyboard
from auto_bot.handlers.status.static_text import *


def get_vehicle_of_driver(update, context):
    driver_ = context.user_data['u_driver']
    vehicles = [i.licence_plate for i in Vehicle.objects.filter(driver=driver_.id, gps_imei__isnull=False)]
    if vehicles:
        if len(vehicles) == 1:
            update.message.reply_text(f'Ви сьогодні на авто з номерним знаком {vehicles[0]}?',
                                      reply_markup=markup_keyboard([choose_auto_keyboard]))
            context.user_data['vehicle'] = vehicles[0]
        else:
            licence_plates = {i.id: i.licence_plate for i in Vehicle.objects.all() if i.licence_plate in vehicles}
            vehicles = {k: licence_plates[k] for k in sorted(licence_plates)}
            context.user_data['data_vehicles'] = vehicles
            report_list_vehicles = ''
            for k, v in vehicles.items():
                report_list_vehicles += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_vehicles}')
            update.message.reply_text(choose_car_text, reply_markup=ReplyKeyboardRemove())
            context.user_data['driver_state'] = V_ID
    else:
        update.message.reply_text("За вами не закріплено жодного авто з gps. Зверніться до вашого менеджера")


def correct_or_not_auto(update, context):
    option = update.message.text
    if option == f'{CORRECT_AUTO}':
        record = UseOfCars.objects.filter(licence_plate=context.user_data['vehicle'],
                                          created_at__date=timezone.localtime().date(),
                                          end_at=None)
        if record:
            update.message.reply_text(already_in_use_text)
        else:
            get_imei(update, context)
    else:
        update.message.reply_text('Зверніться до менеджерів водіїв та проконсультуйтесь,'
                                  ' яку машину вам використовувати сьогодні', reply_markup=ReplyKeyboardRemove())


def correct_choice(update, context):
    id_vehicle = update.message.text
    try:
        id_vehicle = int(id_vehicle)
        if id_vehicle in context.user_data['data_vehicles'].keys():
            licence_plate = Vehicle.objects.get(id=id_vehicle)
            context.user_data['vehicle'] = licence_plate
        else:
            update.message.reply_text(bad_value)
            get_vehicle_of_driver(update, context)
            context.user_data['vehicle'] = None
    except:
        update.message.reply_text(wrong_number_auto_text)
        get_vehicle_of_driver(update, context)
        context.user_data['vehicle'] = None
    if context.user_data['vehicle'] is not None:
        record = UseOfCars.objects.filter(licence_plate=context.user_data['vehicle'],
                                          created_at__date=timezone.localtime().date(),
                                          end_at=None)
        if record:
            update.message.reply_text(already_in_use_text)
            context.user_data['driver_state'] = None
            get_vehicle_of_driver(update, context)
        else:
            update.message.reply_text(f"Ви обрали {context.user_data['vehicle']}. Вірно?",
                                      reply_markup=markup_keyboard([correct_keyboard]))
            context.user_data['driver_state'] = None


def get_imei(update, context):
    chat_id = update.message.chat.id
    UseOfCars.objects.create(
        user_vehicle=context.user_data['u_driver'],
        chat_id=chat_id,
        licence_plate=context.user_data['vehicle'])
    update.message.reply_text(add_auto_to_driver_text, reply_markup=ReplyKeyboardRemove())
    context.user_data['u_driver'].driver_status = Driver.ACTIVE
    context.user_data['u_driver'].save()
    context.user_data.clear()
