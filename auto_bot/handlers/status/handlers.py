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
        update.message.reply_text(f'Зареєструйтесь як водій')


def send_set_status(update, context):

    buttons = [[KeyboardButton(Driver.ACTIVE)],
               [KeyboardButton(Driver.WITH_CLIENT)],
               [KeyboardButton(Driver.WAIT_FOR_CLIENT)],
               [KeyboardButton(Driver.OFFLINE)],
               [KeyboardButton(Driver.RENT)]
               ]

    context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть статус',
                             reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))


def set_status(update, context):
    status = update.message.text
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
    ParkStatus.objects.create(driver=driver, status=status)
    if status == Driver.OFFLINE:
        record = UseOfCars.objects.get(user_vehicle=driver, created_at__date=timezone.now().date(), end_at=None)
        record.end_at = timezone.now()
        record.save()
        update.message.reply_text(f'Ви закінчили працювати, до зустрічі', reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(f'Твій статус: <b>{status}</b>', reply_markup=ReplyKeyboardRemove(), parse_mode=ParseMode.HTML)


CORRECT_AUTO = '- ТАК -'
NOT_CORRECT_AUTO = '- НІ -'


def get_vehicle_of_driver(update, context):
    chat_id = update.message.chat.id
    driver_ = Driver.get_by_chat_id(chat_id)
    context.user_data['u_driver'] = driver_

    keyboard = [[KeyboardButton(f'{CORRECT_AUTO}')],
                [KeyboardButton(f'{NOT_CORRECT_AUTO}')]]

    reply_markup = ReplyKeyboardMarkup(
        keyboard=[keyboard[0], keyboard[1]],
        resize_keyboard=True)

    vehicles = [i.licence_plate for i in Vehicle.objects.filter(driver=driver_.id)]
    if vehicles:
        if len(vehicles) == 1:
            vehicle = Vehicle.objects.get(licence_plate=vehicles[0])
            if vehicle.gps_imei:
                update.message.reply_text(f'Ви сьогодні на авто з номерним знаком {vehicles[0]}?', reply_markup=reply_markup)
                context.user_data['vehicle'] = vehicles[0]
            else:
                update.message.reply_text('За вашим авто не закріпленний imei_gps. Зверніться до менеджера автопарку/водіїв')
        else:
            global STATE_D
            licence_plates = {i.id: i.licence_plate for i in Vehicle.objects.all() if i.licence_plate in vehicles}
            vehicles = {k: licence_plates[k] for k in sorted(licence_plates)}
            context.user_data['data_vehicles'] = vehicles
            report_list_vehicles = ''
            for k, v in vehicles.items():
                report_list_vehicles += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_vehicles}')
            update.message.reply_text(f'Укажіть номер машини, яку ви будете використовувати сьогодні')
            STATE_D = V_CAR
    else:
        update.message.reply_text("За вами не закріплено жодного авто. Зверніться до менеджерів")


def add_vehicle_to_driver(update, context):
    global STATE_D
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
            update.message.reply_text('Ми закріпили авто за вами на сьогодні. Гарного робочого дня')
            ParkStatus.objects.create(driver=context.user_data['u_driver'], status=DRIVER.ACTIVE)
        else:
            update.message.reply_text('За авто, яке ви обрали не закріпленний imei_gps. Зверніться до менеджера автопарку/водіїв')
        STATE_D = None


def correct_or_not_auto(update, context):
    option = update.message.text
    chat_id = update.message.chat.id
    if option == f'{CORRECT_AUTO}':
        record = UseOfCars.objects.filter(licence_plate=context.user_data['use_vehicle'],
                                          created_at__date=timezone.now().date(), end_at=None)
        if record:
            update.message.reply_text('Ваше авто вже використовує інший водій. Зверніться до менеджерів')
        else:
            UseOfCars.objects.create(
                user_vehicle=context.user_data['u_driver'],
                chat_id=chat_id,
                licence_plate=context.user_data['vehicle'])
            update.message.reply_text('Ми закріпили авто за вами на сьогодні і вже шукаємо замовлення. \
                                       Гарного робочого дня', reply_markup=ReplyKeyboardRemove())
            ParkStatus.objects.create(driver=context.user_data['u_driver'], status=DRIVER.ACTIVE)
    else:
        update.message.reply_text('Зверніться до менеджерів водіїв та проконсультуйтесь, яку машину вам використовувати сьогодні.' +
                                  ' Та скористайтесь наступною командою /car_change', reply_markup=ReplyKeyboardRemove())


def get_vehicle_licence_plate(update, context):
    global STATE_D
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
            STATE_D = V_ID
        else:
            update.message.reply_text("Не здайдено жодного авто у автопарку. Зверніться до Менеджера автопарку", reply_markup=ReplyKeyboardRemove())
    else:
        update.message.reply_text(f'Зареєструйтесь як водій')


CORRECT_CHOICE = 'Так'
NOT_CORRECT_CHOICE = 'Ні'


def correct_choice(update, context):
    global STATE_D
    STATE_D = None
    id_vehicle = update.message.text
    try:
        id_vehicle = int(id_vehicle)
        context.user_data['vehicle'] = Vehicle.objects.get(id=id_vehicle)
    except:
        update.message.reply_text('Не вдалось обробити ваше значення, або переданий номер автомобільного номера виявився недійсним. Спробуйте ще раз')
        context.user_data['vehicle'] = False
    if context.user_data['vehicle']:
        keyboard = [KeyboardButton(f'{CORRECT_CHOICE}'),
                    KeyboardButton(f'{NOT_CORRECT_CHOICE}')]

        reply_markup = ReplyKeyboardMarkup(
            keyboard=[keyboard],
            resize_keyboard=True)
        licence_plate = context.user_data['vehicle']
        update.message.reply_text(f"Ви обрали {licence_plate}. Вірно?", reply_markup=reply_markup)


def get_imei(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id=chat_id)
    if context.user_data['vehicle'].gps_imei:
        UseOfCars.objects.create(
            user_vehicle=driver,
            chat_id=chat_id,
            licence_plate=context.user_data['vehicle'])
        update.message.reply_text('Ми закріпили авто за вами на сьогодні. Гарного робочого дня', reply_markup=ReplyKeyboardRemove())
        ParkStatus.objects.create(driver=context.user_data['u_driver'], status=DRIVER.ACTIVE)
    else:
        update.message.reply_text('Авто яке ви обрали без imei_gps. Зверніться до менеджера автопарку/водіїв', reply_markup=ReplyKeyboardRemove())



def get_licence_plate_for_gps_imei(update, context):
    global STATE_DM
    chat_id = update.message.chat.id
    driver_manager = DriverManager.get_by_chat_id(chat_id)
    vehicles = {i.id: i.licence_plate for i in Vehicle.objects.all()}
    vehicles = {k: vehicles[k] for k in sorted(vehicles)}
    report_list_vehicles = ''
    if driver_manager is not None:
        if vehicles:
            for k, v in vehicles.items():
                report_list_vehicles += f'{k}: {v}\n'
            update.message.reply_text(f'{report_list_vehicles}')
            update.message.reply_text(f'Укажіть номер машини від 1-{len(vehicles)}, для якого ви бажаєте добавити gps_imei')
            STATE_DM = V_GPS
        else:
            update.message.reply_text("Не здайдено жодного авто у автопарку")
    else:
        update.message.reply_text('Зареєструйтесь як менеджер водіїв')


def get_n_vehicle(update, context):
    global STATE_DM
    id_vehicle = update.message.text
    try:
        id_vehicle = int(id_vehicle)
        context.user_data['vehicle'] = Vehicle.objects.get(id=id_vehicle)
        update.message.reply_text('Введіть gps_imei для данного авто')
        STATE_DM = V_GPS_IMEI
    except:
        update.message.reply_text('Не вдалось обробити ваше значення, або переданий номер автомобільного номера виявився недійсним. Спробуйте ще раз')


def get_gps_imea(update, context):
    global STATE_DM
    gps_imei = update.message.text
    gps_imei = Vehicle.gps_imei_validator(gps_imei=gps_imei)
    if gps_imei is not None:
        context.user_data['vehicle'].gps_imei = gps_imei
        context.user_data['vehicle'].save()
        update.message.reply_text('Ми встановили GPS imei до авто, яке ви вказали')
        STATE_DM = None
    else:
        update.message.reply_text("Задовне значення. Спробуйте ще раз")