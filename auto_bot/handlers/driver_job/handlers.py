import datetime
import os
import threading
import time

import redis
from telegram import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler

from app.models import User, JobApplication
from auto_bot.handlers.driver_job.keyboards import job_name_buttons
from auto_bot.handlers.driver_job.static_text import JOB_DRIVER
from auto_bot.handlers.main.keyboards import markup_keyboard_onetime


def job_application(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Оберіть посаду на яку ви притендуєте:',
                             reply_markup=markup_keyboard_onetime(job_name_buttons))
    update.message.reply_text(
        "Якщо ви десь помилитесь, ви завжди можете почати спочатку, скориставшись командою /restart")


def restart_job_application(update, context):
    context.user_data.clear()
    context.user_data['role'] = f"{JOB_DRIVER}"
    update.message.reply_text("Ви почали подачу заявки спочатку.")
    update.message.reply_text("Введіть ваше Ім`я:")
    return "JOB_USER_NAME"


# Update information for users
def update_name(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    context.user_data['role'] = f"{JOB_DRIVER}"
    if user:
        update.message.reply_text("Введіть ваше Ім`я:", reply_markup=ReplyKeyboardRemove())
        return "JOB_USER_NAME"
    else:
        update.message.reply_text('Спочатку надайте телефон')


def update_second_name(update, context):
    name = update.message.text
    clear_name = User.name_and_second_name_validator(name=name)
    if clear_name is not None:
        context.user_data['u_name'] = clear_name
        update.message.reply_text("Введіть Прізвище:")
        return "JOB_LAST_NAME"
    else:
        update.message.reply_text('Ім`я занадто довге. Спробуйте ще раз')
        return "JOB_USER_NAME"


def update_email(update, context):
    second_name = update.message.text
    clear_second_name = User.name_and_second_name_validator(name=second_name)
    if clear_second_name is not None:
        context.user_data['u_second_name'] = clear_second_name
        update.message.reply_text("Введіть електронну адресу:")
        return "JOB_EMAIL"
    else:
        update.message.reply_text('Прізвище занадто довге. Спробуйте ще раз')
        return "JOB_LAST_NAME"


def update_user_information(update, context):
    email = update.message.text
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    clear_email = User.email_validator(email=email)
    context.user_data['phone'] = user.phone_number
    if clear_email is not None:
        user.name = context.user_data['u_name']
        user.second_name = context.user_data['u_second_name']
        user.email = clear_email
        user.save()
        buttons = [[InlineKeyboardButton(text='Завантажити документи', callback_data='job_photo')]]
        update.message.reply_text(
            'Ваші дані оновлені, надайте будь-ласка необхідні документи, скориставшись кнопкою під повідомленням',
            reply_markup=InlineKeyboardMarkup(buttons))
        return "WAIT_FOR_JOB_OPTION"
    else:
        update.message.reply_text('Eлектронна адреса некоректна. Спробуйте ще раз')
        return 'JOB_EMAIL'


def get_job_photo(update, context):
    update.callback_query.answer()
    update.callback_query.edit_message_text(
        text='Надішліть ваше фото не розмите, без головного убору та окулярів (селфі).Для відправки скористайтеся \U0001F4CE біля menu')
    return 'WAIT_FOR_JOB_PHOTO'


def upload_photo(update, context):
    os.makedirs('data/mediafiles/job/photo/', exist_ok=True)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'data/mediafiles/job/photo/{image["file_unique_id"]}.jpg'
        context.user_data['photo_job'] = f'job/photo/{image["file_unique_id"]}.jpg'
        image.download(filename)
        update.message.reply_text('Ваше фото збережено.Надішліть лицьову сторону посвідчення')
        context.bot.send_photo(update.effective_chat.id,
                               'https://kourier.in.ua/uploads/posts/2016-12/1480604684_1702.jpg')
        return 'WAIT_FOR_FRONT_PHOTO'
    else:
        update.message.reply_text('Будь ласка, надішліть фото (селфі).Для відправки скористайтеся \U0001F4CE біля menu',
                                  reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_JOB_PHOTO'


def upload_license_front_photo(update, context):
    os.makedirs('data/mediafiles/job/licenses/front/', exist_ok=True)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'data/mediafiles/job/licenses/front/{image["file_unique_id"]}.jpg'
        context.user_data['front_license'] = f'job/licenses/front/{image["file_unique_id"]}.jpg'
        image.download(filename)
        update.message.reply_text('Лицьова сторона посвідчення збережена.Надішліть тильну сторону')
        context.bot.send_photo(update.effective_chat.id,
                               'https://www.autoconsulting.com.ua/pictures/_upload/1582561870fbTo_h.jpg')
        return 'WAIT_FOR_BACK_PHOTO'
    else:
        update.message.reply_text('Будь ласка, надішліть лицьову сторону', reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_FRONT_PHOTO'


def upload_license_back_photo(update, context):
    os.makedirs('data/mediafiles/job/licenses/back/', exist_ok=True)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'data/mediafiles/job/licenses/back/{image["file_unique_id"]}.jpg'
        context.user_data['back_license'] = f'job/licenses/back/{image["file_unique_id"]}.jpg'
        image.download(filename)
        update.message.reply_text(
            'Тильна сторона посвідчення збережена.Надішліть срок дії посвідчення у форматі рік-місяць-день (наприклад: 1999-05-25).')
        update.message.reply_text(
            'Якщо посвідчення безстрокове введіть 2077-12-31 або будь-яку іншу дату у далекому майбутньому до 2077р.:')
        return 'WAIT_FOR_EXPIRED'
    else:
        update.message.reply_text('Будь ласка, надішліть тильну сторону', reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_BACK_PHOTO'


def upload_expired_date(update, context):
    date = update.message.text
    if JobApplication.validate_date(date):
        context.user_data['expired_license'] = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        buttons = [[InlineKeyboardButton(text='так', callback_data='have_auto')],
                   [InlineKeyboardButton(text='ні', callback_data='no_auto')]]
        update.message.reply_text('Чи є у вас авто для роботи:', reply_markup=InlineKeyboardMarkup(buttons))
        return "WAIT_ANSWER"
    else:
        update.message.reply_text(
            f'{date} не вірний формат або дата, Надішліть срок дії посвідчення у форматі рік-місяць-день (наприклад: 1999-05-25):')
        return 'WAIT_FOR_EXPIRED'


def check_auto(update, context):
    query = update.callback_query
    if query.data == 'have_auto':
        query.answer()
        query.edit_message_text('Дякуємо! Будь ласка, надішліть фото посвідчення про реєстрацію авто.',
                                reply_markup=None)
        context.bot.send_photo(query.message.chat_id,
                               'https://protocol.ua/userfiles/tehpasport-na-avto.jpg')
        return 'WAIT_FOR_AUTO_YES_OPTION'
    else:
        chat_id = update.effective_chat.id
        user = User.get_by_chat_id(chat_id)
        try:
            JobApplication.objects.get(phone_number=user.phone_number)
            update.message.reply_text('Ви вже подали заявку.Очікуйте дзвінка від нашого менеджера')
        except JobApplication.DoesNotExist:
            JobApplication.objects.create(
                first_name=user.name,
                last_name=user.second_name,
                email=user.email,
                phone_number=user.phone_number,
                license_expired=context.user_data['expired_license'],
                driver_license_front=context.user_data['front_license'],
                driver_license_back=context.user_data['back_license'],
                photo=context.user_data['photo_job'],
                role=context.user_data['role'])
        finally:
            query.edit_message_text(
                f'Заявка сформована.На номер {user.phone_number} відправлено СМС перешліть чотири цифри коду мені будь-ласка')
            context.user_data['thread'] = True
            t = threading.Thread(target=code_timer, args=(update, context, 180, 30), daemon=True)
            t.start()
            return "JOB_UKLON_CODE"


def upload_auto_doc(update, context):
    os.makedirs('data/mediafiles/job/car/', exist_ok=True)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'data/mediafiles/job/car/{image["file_unique_id"]}.jpg'
        context.user_data['auto_doc'] = f'job/car/{image["file_unique_id"]}.jpg'
        image.download(filename)
        update.message.reply_text('Якщо щось пішло не так, ви можете почати спочатку за допомогою команди /restart')
        update.message.reply_text(
            'Фото техпаспорту збережено.Надішліть фото автоцивілки')
        context.bot.send_photo(update.effective_chat.id,
                               'https://rinokstrahovka.ua/img/content/2019/07/paper_client_green1.jpg')
        return 'WAIT_FOR_INSURANCE'
    else:
        update.message.reply_text('Будь ласка, надішліть фото техпаспорту', reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_AUTO_YES_OPTION'


def upload_insurance(update, context):
    os.makedirs('data/mediafiles/job/insurance/', exist_ok=True)
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'data/mediafiles/job/insurance/{image["file_unique_id"]}.jpg'
        context.user_data['insurance'] = f'job/insurance/{image["file_unique_id"]}.jpg'
        image.download(filename)
        update.message.reply_text(
            'Фото автоцивілки збережено.Надішліть срок дії автоцивілки у форматі рік-місяць-день (наприклад: 1999-05-25):')
        return 'WAIT_FOR_INSURANCE_EXPIRED'
    else:
        update.message.reply_text('Будь ласка, надішліть фото автоцивілки', reply_markup=ReplyKeyboardRemove())
        return 'WAIT_FOR_INSURANCE'


def upload_expired_insurance(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    date = update.message.text
    if JobApplication.validate_date(date):
        context.user_data['expired_insurance'] = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        try:
            JobApplication.objects.get(phone_number=user.phone_number)
            update.message.reply_text('Ви вже подали заявку.Очікуйте дзвінка від нашого менеджера')
        except JobApplication.DoesNotExist:
            JobApplication.objects.create(
                first_name=user.name,
                last_name=user.second_name,
                email=user.email,
                phone_number=user.phone_number,
                license_expired=context.user_data['expired_license'],
                driver_license_front=context.user_data['front_license'],
                driver_license_back=context.user_data['back_license'],
                photo=context.user_data['photo_job'],
                role=context.user_data['role'],
                car_documents=context.user_data['auto_doc'],
                insurance=context.user_data['insurance'],
                insurance_expired=context.user_data['expired_insurance']
            )
        finally:
            context.user_data['thread'] = True
            t = threading.Thread(target=code_timer, args=(update, context, 180, 30), daemon=True)
            t.start()
            update.message.reply_text(
                f'Заявка сформована.На номер {user.phone_number} відправлено СМС перешліть чотири цифри коду нам протягом 3 хвилин будь-ласка')
            return "JOB_UKLON_CODE"
    else:
        update.message.reply_text(
            f'{date} не вірний формат або дата, Надішліть срок дії посвідчення у форматі рік-місяць-день (наприклад: 1999-05-25):')
        return 'WAIT_FOR_EXPIRED'


def uklon_code(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    context.user_data['thread'] = False
    r = redis.Redis.from_url(os.environ["REDIS_URL"])
    r.publish(f'{user.phone_number} code', update.message.text)
    update.message.reply_text(
        'Ваш код прийнято.Наш менеджер з вами зв\'яжеться.Не забудьте зареєструватись на сайті https://supplier.uber.com, як водій')
    return ConversationHandler.END


def code_timer(update, context, timer, sleep):
    def timer_callback(context):
        context.bot.send_message(update.effective_chat.id,
                                 f'Заявку відхилено.Ви завжди можете подати її повторно')
        JobApplication.objects.filter(phone_number=context.user_data['phone']).first().delete()
        return ConversationHandler.END

    remaining_time = timer
    while remaining_time > 0:
        try:
            tread_state = context.user_data['thread']
            if tread_state:
                if remaining_time < sleep + 1:
                    context.bot.send_message(update.effective_chat.id,
                                             f'Залишилось {int(remaining_time)} секунд.Якщо ви не відправите код заявку буде скасовано')
                    time.sleep(remaining_time)
                    remaining_time = 0
                    timer_callback(context)
                else:
                    context.bot.send_message(update.effective_chat.id,
                                             f'Коду лишилось діяти {int(remaining_time)} секунд.Поспішіть будь-ласка')
                    time.sleep(sleep)
                    remaining_time = int(remaining_time - sleep)
            else:
                break
        except KeyError:
            break
