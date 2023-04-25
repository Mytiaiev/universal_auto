STATE_D = None    # range(50 - 100)
NUMBERPLATE, REPORT, V_ID, V_CAR = range(50, 54)


# Changing status car
def status_car(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:
        buttons = [[KeyboardButton(f'{SERVICEABLE}')], [KeyboardButton(f'{BROKEN}')]]
        context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть статус автомобіля',
                                        reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
    else:
        update.message.reply_text(f'Зареєструтесь як водій', reply_markup=ReplyKeyboardRemove())


def numberplate(update, context):
    global STATE_D
    context.user_data['status'] = update.message.text
    update.message.reply_text('Введіть номер автомобіля', reply_markup=ReplyKeyboardRemove())
    STATE_D = NUMBERPLATE


def change_status_car(update, context):
    global STATE_D
    context.user_data['licence_place'] = update.message.text.upper()
    number_car = context.user_data['licence_place']
    numberplates = [i.licence_plate for i in Vehicle.objects.all()]
    if number_car in numberplates:
        vehicle = Vehicle.get_by_numberplate(number_car)
        vehicle.car_status = context.user_data['status']
        vehicle.save()
        numberplates.clear()
        update.message.reply_text('Статус авто був змінений')
    else:
        update.message.reply_text('Цього номера немає в базі даних або надіслано неправильні дані. Зверніться до менеджера або повторіть команду')

    STATE_D = None


SEND_REPORT_DEBT = 'Надіслати звіт про оплату заборгованості'


# Sending report for drivers(payment debt)
def sending_report(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    if driver is not None:
        buttons = [[InlineKeyboardButton(text=f'{SEND_REPORT_DEBT}', callback_data='photo_debt')]]
        context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть опцію:',
                                 reply_markup=InlineKeyboardMarkup(buttons))
        return "WAIT_FOR_DEBT_OPTION"
    else:
        update.message.reply_text(f'Зареєструтесь як водій', reply_markup=ReplyKeyboardRemove())


def get_debt_photo(update, context):
    empty_inline_keyboard = InlineKeyboardMarkup([])
    update.callback_query.answer()
    update.callback_query.edit_message_text(text='Надішліть фото оплати заборгованості', reply_markup=empty_inline_keyboard)
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


def option(update, context):
    chat_id = update.message.chat.id
    driver = Driver.get_by_chat_id(chat_id)
    keyboard = [KeyboardButton(text=f"{SIGN_UP_FOR_A_SERVICE_CENTER}"),
                KeyboardButton(text=f"{REPORT_CAR_DAMAGE}"),
                KeyboardButton(text=f"{TAKE_A_DAY_OFF}"),
                KeyboardButton(text=f"{TAKE_SICK_LEAVE}")]
    if driver is not None:
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[keyboard],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        update.message.reply_text('Оберіть опцію: ', reply_markup=reply_markup)
    else:
        update.message.reply_text(f'Зареєструтесь як водій', reply_markup=ReplyKeyboardRemove())

TAKE_A_DAY_OFF = 'Взяти вихідний'
TAKE_SICK_LEAVE = 'Взяти лікарняний'
SIGN_UP_FOR_A_SERVICE_CENTER = 'Записатись до сервісного центру'
REPORT_CAR_DAMAGE = 'Оповістити про пошкодження авто'


def take_a_day_off_or_sick_leave(update, context):
    event = update.message.text
    chat_id = update.message.chat.id
    event = event.split()
    driver = Driver.get_by_chat_id(chat_id)
    events = Event.objects.filter(full_name_driver=driver, status_event=False)
    list_event = [i for i in events]
    if len(list_event) > 0:
        update.message.reply_text(f"У вас вже відкритий <<Лікарняний>> або <<Вихідний>>.\nЩоб закрити подію скористайтесь командою /status")
    else:
        driver.driver_status = f'{Driver.OFFLINE}'
        driver.save()
        Event.objects.create(
                full_name_driver=driver,
                event=event[1].title(),
                chat_id=chat_id,
                created_at=datetime.datetime.now())
        update.message.reply_text(f'Ваш статус зміненно на <<{Driver.OFFLINE}>> та ваш <<{event[1].title()}>> розпочато',
                                            reply_markup=ReplyKeyboardRemove())