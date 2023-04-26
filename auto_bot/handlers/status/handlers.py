from django.utils import timezone
from telegram import ReplyKeyboardRemove, ParseMode

from app.models import Vehicle, Driver, UseOfCars, Event, ParkStatus
from auto_bot.handlers.driver.static_text import not_driver_text, V_CAR, V_ID
from auto_bot.handlers.driver_manager.handlers import DRIVER
from auto_bot.handlers.main.keyboards import markup_keyboard_onetime, markup_keyboard
from auto_bot.handlers.status.keyboards import status_buttons, choose_auto_keyboard, correct_keyboard
from auto_bot.handlers.status.static_text import CORRECT_AUTO


def status(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:
        record = UseOfCars.objects.filter(user_vehicle=driver,
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
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    try:
        events = Event.objects.filter(full_name_driver=driver, status_event=False)
        event = [i for i in events]
        event[-1].status_event = True
        event[-1].save()
        update.message.reply_text(f'{driver}: Ваш - {event[-1].event} завершено')
    except:
        pass
    ParkStatus.objects.create(driver=driver, status=driver_status)
    if status == Driver.OFFLINE:
        record = UseOfCars.objects.get(user_vehicle=driver, created_at__date=timezone.now().date(), end_at=None)
        record.end_at = timezone.now()
        record.save()
        update.message.reply_text(f'Ви закінчили працювати, до зустрічі', reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(f'Твій статус: <b>{driver_status}</b>', reply_markup=ReplyKeyboardRemove(),
                                  parse_mode=ParseMode.HTML)


def get_vehicle_of_driver(update, context):
    chat_id = update.message.chat.id
    driver_ = Driver.get_by_chat_id(chat_id)
    context.user_data['u_driver'] = driver_
    vehicles = [i.licence_plate for i in Vehicle.objects.filter(driver=driver_.id)]
    if vehicles:
        if len(vehicles) == 1:
            vehicle = Vehicle.objects.get(licence_plate=vehicles[0])
            if vehicle.gps_imei:
                update.message.reply_text(f'Ви сьогодні на авто з номерним знаком {vehicles[0]}?',
                                          reply_markup=markup_keyboard([choose_auto_keyboard]))
                context.user_data['vehicle'] = vehicles[0]
            else:
                update.message.reply_text('За вашим авто не закріпленний imei_gps. Зверніться до менеджера автопарку/водіїв')
        else:
            licence_plates = {i.id: i.licence_plate for i in Vehicle.objects.all() if i.licence_plate in vehicles}
            vehicles = {k: licence_plates[k] for k in sorted(licence_plates)}
            context.user_data['data_vehicles'] = vehicles
            report_list_vehicles = ''
            for k, v in vehicles.items():
                report_list_vehicles += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_vehicles}')
            update.message.reply_text(f'Укажіть номер машини, яку ви будете використовувати сьогодні')
            context.user_data['driver_state'] = V_CAR
    else:
        update.message.reply_text("За вами не закріплено жодного авто. Зверніться до менеджерів")


def add_vehicle_to_driver(update, context):
    id_vehicle = update.message.text
    chat_id = update.message.chat.id
    try:
        id_vehicle = int(id_vehicle)
        if id_vehicle in context.user_data['data_vehicles']:
            vehicle = Vehicle.objects.get(id=id_vehicle)
        else:
            update.message.reply_text('Такого ключа немає у вашому списку, спробуйте ще раз')
    except:
        update.message.reply_text('Не вдалось обробити ваше значення, або переданий номер автомобільного номера виявився недійсним. Спробуйте ще раз')
    record = UseOfCars.objects.filter(licence_plate=vehicle, created_at__date=timezone.now().date(), end_at=None)
    if record:
        update.message.reply_text('Це авто вже використовує інший водій. Спробуйте інше авто. Якщо всі авто заняті зверніться до менеджерів')
        get_vehicle_of_driver(update, context)
    else:
        if vehicle.gps_imei:
            UseOfCars.objects.create(
                user_vehicle=context.user_data['u_driver'],
                chat_id=chat_id,
                licence_plate=vehicle)
            update.message.reply_text('Ми закріпили авто за вами на сьогодні. Гарного робочого дня',
                                      reply_markup=ReplyKeyboardRemove())
            ParkStatus.objects.create(driver=context.user_data['u_driver'], status=Driver.ACTIVE)
        else:
            update.message.reply_text('За авто, яке ви обрали не закріпленний imei_gps. Зверніться до менеджера автопарку/водіїв')
        context.user_data['driver_state'] = None


def correct_or_not_auto(update, context):
    option = update.message.text
    chat_id = update.message.chat.id
    if option == f'{CORRECT_AUTO}':
        record = UseOfCars.objects.filter(licence_plate=context.user_data['vehicle'],
                                          created_at__date=timezone.now().date(), end_at=None)
        if record:
            update.message.reply_text('Ваше авто вже використовує інший водій. Зверніться до менеджерів', reply_markup=ReplyKeyboardRemove())
        else:
            UseOfCars.objects.create(
                user_vehicle=context.user_data['u_driver'],
                chat_id=chat_id,
                licence_plate=context.user_data['vehicle'])
            update.message.reply_text('Ми закріпили авто за вами на сьогодні і вже шукаємо замовлення. \
                                       Гарного робочого дня', reply_markup=ReplyKeyboardRemove())
            ParkStatus.objects.create(driver=context.user_data['u_driver'], status=Driver.ACTIVE)
    else:
        update.message.reply_text('Зверніться до менеджерів водіїв та проконсультуйтесь, яку машину вам використовувати сьогодні.' +
                                  ' Та скористайтесь наступною командою /car_change', reply_markup=ReplyKeyboardRemove())


def get_vehicle_licence_plate(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:
        vehicles = {i.id: i.licence_plate for i in Vehicle.objects.all()}
        vehicles = {k: vehicles[k] for k in sorted(vehicles)}
        report_list_vehicles = ''
        if vehicles:
            for k, v in vehicles.items():
                report_list_vehicles += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_vehicles}')
            update.message.reply_text(f'Укажіть номер машини від 1-{len(vehicles)}, яку ви будете використовувати сьогодні', reply_markup=ReplyKeyboardRemove())
            context.user_data['driver_state'] = V_ID
        else:
            update.message.reply_text("Не здайдено жодного авто у автопарку. Зверніться до Менеджера автопарку", reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(not_driver_text)


def correct_choice(update, context):
    context.user_data['driver_state'] = None
    id_vehicle = update.message.text
    try:
        id_vehicle = int(id_vehicle)
        context.user_data['vehicle'] = Vehicle.objects.get(id=id_vehicle)
    except:
        update.message.reply_text('Не вдалось обробити ваше значення, або переданий номер автомобільного номера виявився недійсним. Спробуйте ще раз')
        context.user_data['vehicle'] = False
    if context.user_data['vehicle']:
        licence_plate = context.user_data['vehicle']
        update.message.reply_text(f"Ви обрали {licence_plate}. Вірно?", reply_markup=markup_keyboard([correct_keyboard]))


def get_imei(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id=chat_id)
    if context.user_data['vehicle'].gps_imei:
        UseOfCars.objects.create(
            user_vehicle=driver,
            chat_id=chat_id,
            licence_plate=context.user_data['vehicle'])
        update.message.reply_text('Ми закріпили авто за вами на сьогодні. Гарного робочого дня', reply_markup=ReplyKeyboardRemove())
        ParkStatus.objects.create(driver=context.user_data['u_driver'], status=Driver.ACTIVE)
    else:
        update.message.reply_text('Авто яке ви обрали без imei_gps. Зверніться до менеджера автопарку/водіїв', reply_markup=ReplyKeyboardRemove())



