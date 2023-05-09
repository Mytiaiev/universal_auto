from django.utils import timezone
from telegram import ReplyKeyboardRemove, ParseMode
from app.models import Vehicle, Driver, UseOfCars, Event, ParkStatus
from auto_bot.handlers.driver.static_text import not_driver_text, V_ID
from auto_bot.handlers.main.keyboards import markup_keyboard_onetime, markup_keyboard
from auto_bot.handlers.status.keyboards import status_buttons, choose_auto_keyboard, correct_keyboard
from auto_bot.handlers.status.static_text import CORRECT_AUTO, already_in_use_text, add_auto_to_driver_text, \
    wrong_number_auto_text, choose_car_text


def status(update, context):
    chat_id = update.message.chat.id
    context.user_data['u_driver'] = Driver.get_by_chat_id(chat_id)
    if context.user_data['u_driver'] is not None:
        record = UseOfCars.objects.filter(user_vehicle=context.user_data['u_driver'],
                                          created_at__date=timezone.now().date(),
                                          end_at=None)
        if record:
            send_set_status(update, context)
        else:
            get_vehicle_of_driver(update, context)
    else:
        update.message.reply_text(not_driver_text)


def send_set_status(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть статус',
                             reply_markup=markup_keyboard_onetime(status_buttons))


def set_status(update, context):
    driver_status = update.message.text
    try:
        events = Event.objects.filter(full_name_driver=context.user_data['u_driver'], status_event=False)
        event = [i for i in events]
        event[-1].status_event = True
        event[-1].save()
        update.message.reply_text(f"{context.user_data['u_driver']}: Ваш - {event[-1].event} завершено")
    except IndexError:
        pass
    ParkStatus.objects.create(driver=context.user_data['u_driver'], status=driver_status)
    if driver_status == Driver.OFFLINE:
        record = UseOfCars.objects.get(user_vehicle=context.user_data['u_driver'],
                                       created_at__date=timezone.now().date(), end_at=None)
        record.end_at = timezone.now()
        record.save()
        update.message.reply_text(f'Ви закінчили працювати, до зустрічі', reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(f'Твій статус: <b>{driver_status}</b>', reply_markup=ReplyKeyboardRemove(),
                                  parse_mode=ParseMode.HTML)


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
            update.message.reply_text(choose_car_text)
            context.user_data['driver_state'] = V_ID
    else:
        update.message.reply_text("За вами не закріплено жодного авто з gps. Зверніться до менеджерів")


def correct_or_not_auto(update, context):
    option = update.message.text
    if option == f'{CORRECT_AUTO}':
        correct_choice(update, context)
    else:
        update.message.reply_text('Зверніться до менеджерів водіїв та проконсультуйтесь,'
                                  ' яку машину вам використовувати сьогодні.'
                                  'Та скористайтесь наступною командою /car_change', reply_markup=ReplyKeyboardRemove())


def get_vehicle_licence_plate(update, context):
    context.user_data['vehicle'] = None
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:
        vehicles = {i.id: i.licence_plate for i in Vehicle.objects.filter(gps_imei__isnull=False)}
        vehicles = {k: vehicles[k] for k in sorted(vehicles)}
        report_list_vehicles = ''
        if vehicles:
            for k, v in vehicles.items():
                report_list_vehicles += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_vehicles}')
            update.message.reply_text(choose_car_text, reply_markup=ReplyKeyboardRemove())
            context.user_data['driver_state'] = V_ID
        else:
            update.message.reply_text("Не здайдено жодного авто у автопарку. Зверніться до Менеджера автопарку",
                                      reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(not_driver_text)


def correct_choice(update, context):
    if context.user_data.get('vehicle') is None:
        context.user_data['driver_state'] = None
        id_vehicle = update.message.text
        try:
            id_vehicle = int(id_vehicle)
            licence_plate = Vehicle.objects.filter(id=id_vehicle).first()
            context.user_data['vehicle'] = licence_plate
        except ValueError:
            update.message.reply_text(wrong_number_auto_text)
    record = UseOfCars.objects.filter(licence_plate=context.user_data['vehicle'],
                                      created_at__date=timezone.now().date(),
                                      end_at=None)
    if record:
        update.message.reply_text(already_in_use_text)
        get_vehicle_of_driver(update, context)
    else:
        update.message.reply_text(f"Ви обрали {context.user_data['vehicle']}. Вірно?",
                                  reply_markup=markup_keyboard([correct_keyboard]))


def get_imei(update, context):
    chat_id = update.message.chat.id
    UseOfCars.objects.create(
        user_vehicle=context.user_data['u_driver'],
        chat_id=chat_id,
        licence_plate=context.user_data['vehicle'])
    update.message.reply_text(add_auto_to_driver_text, reply_markup=ReplyKeyboardRemove())
    ParkStatus.objects.create(driver=context.user_data['u_driver'], status=Driver.ACTIVE)
