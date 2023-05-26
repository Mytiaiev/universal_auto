import datetime
import io
import os
import threading
import time

import redis
from google.cloud import storage
from telegram import ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ConversationHandler

from app.models import User, JobApplication
from auto import settings
from auto_bot.handlers.driver_job.keyboards import job_name_buttons, inline_ask_auto_kb
from auto_bot.handlers.driver_job.static_text import *
from auto_bot.handlers.main.keyboards import markup_keyboard_onetime


def job_application(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=choose_job,
                             reply_markup=markup_keyboard_onetime(job_name_buttons))
    update.message.reply_text(make_mistake_text)


def restart_job_application(update, context):
    context.user_data.clear()
    context.user_data['role'] = f"{JOB_DRIVER}"
    update.message.reply_text(start_again_text)
    update.message.reply_text(ask_name_text)
    return "JOB_USER_NAME"


# Update information for users
def update_name(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    context.user_data['role'] = f"{JOB_DRIVER}"
    if user:
        try:
            JobApplication.objects.get(phone_number=user.phone_number)
            update.message.reply_text(already_send_text)
        except JobApplication.DoesNotExist:
            update.message.reply_text(ask_name_text, reply_markup=ReplyKeyboardRemove())
            return "JOB_USER_NAME"
    else:
        update.message.reply_text(no_phone_text)


def update_second_name(update, context):
    name = update.message.text
    clear_name = User.name_and_second_name_validator(name=name)
    if clear_name is not None:
        context.user_data['u_name'] = clear_name
        update.message.reply_text(ask_lastname_text)
        return "JOB_LAST_NAME"
    else:
        update.message.reply_text(no_valid_name_text)
        return "JOB_USER_NAME"


def update_email(update, context):
    second_name = update.message.text
    clear_second_name = User.name_and_second_name_validator(name=second_name)
    if clear_second_name is not None:
        context.user_data['u_second_name'] = clear_second_name
        update.message.reply_text(ask_email_text)
        return "JOB_EMAIL"
    else:
        update.message.reply_text()
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
        update.message.reply_text(updated_text, reply_markup=InlineKeyboardMarkup(buttons))
        return "WAIT_FOR_JOB_OPTION"
    else:
        update.message.reply_text(no_valid_email_text)
        return 'JOB_EMAIL'


def get_job_photo(update, context):
    update.callback_query.edit_message_text(text=ask_photo_text)
    return 'WAIT_FOR_JOB_PHOTO'


def upload_photo(update, context):
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'job/photo/{image["file_unique_id"]}.jpg'
        context.user_data['photo_job'] = filename
        save_storage_photo(image, filename)
        update.message.reply_text(saved_photo_text)
        context.bot.send_photo(update.effective_chat.id,
                               'https://kourier.in.ua/uploads/posts/2016-12/1480604684_1702.jpg')
        return 'WAIT_FOR_FRONT_PHOTO'
    else:
        update.message.reply_text(no_photo_text)
        return 'WAIT_FOR_JOB_PHOTO'


def upload_license_front_photo(update, context):
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'job/licenses/front/{image["file_unique_id"]}.jpg'
        context.user_data['front_license'] = filename
        save_storage_photo(image, filename)
        update.message.reply_text(front_licence_saved)
        context.bot.send_photo(update.effective_chat.id,
                               'https://www.autoconsulting.com.ua/pictures/_upload/1582561870fbTo_h.jpg')
        return 'WAIT_FOR_BACK_PHOTO'
    else:
        update.message.reply_text(ask_front_licence)
        return 'WAIT_FOR_FRONT_PHOTO'


def upload_license_back_photo(update, context):
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'job/licenses/back/{image["file_unique_id"]}.jpg'
        context.user_data['back_license'] = filename
        save_storage_photo(image, filename)
        update.message.reply_text(back_licence_saved)
        update.message.reply_text(no_date_licence)
        return 'WAIT_FOR_EXPIRED'
    else:
        update.message.reply_text(ask_back_licence)
        return 'WAIT_FOR_BACK_PHOTO'


def upload_expired_date(update, context):
    date = update.message.text
    if JobApplication.validate_date(date):
        context.user_data['expired_license'] = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        update.message.reply_text(ask_auto_text, reply_markup=inline_ask_auto_kb())
        return "WAIT_ANSWER"
    else:
        update.message.reply_text(f'{date} {no_valid_date_text}')
        return 'WAIT_FOR_EXPIRED'


def check_auto(update, context):
    query = update.callback_query
    query.edit_message_text(ask_autodoc_text)
    context.bot.send_photo(query.message.chat_id,
                           'https://protocol.ua/userfiles/tehpasport-na-avto.jpg')
    return 'WAIT_FOR_AUTO_YES_OPTION'


def upload_auto_doc(update, context):
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'job/car/{image["file_unique_id"]}.jpg'
        context.user_data['auto_doc'] = filename
        save_storage_photo(image, filename)
        update.message.reply_text(make_mistake_text)
        update.message.reply_text(autodoc_saved_text)
        context.bot.send_photo(update.effective_chat.id,
                               'https://rinokstrahovka.ua/img/content/2019/07/paper_client_green1.jpg')
        return 'WAIT_FOR_INSURANCE'
    else:
        update.message.reply_text(no_autodoc_text)
        return 'WAIT_FOR_AUTO_YES_OPTION'


def upload_insurance(update, context):
    if update.message.photo:
        image = update.message.photo[-1].get_file()
        filename = f'job/insurance/{image["file_unique_id"]}.jpg'
        context.user_data['insurance'] = filename
        save_storage_photo(image, filename)
        update.message.reply_text(insurance_saved_text)
        return 'WAIT_FOR_INSURANCE_EXPIRED'
    else:
        update.message.reply_text(ask_insurance_photo)
        return 'WAIT_FOR_INSURANCE'


def upload_expired_insurance(update, context):
    query = update.callback_query
    chat_id = update.effective_chat.id
    user = User.get_by_chat_id(chat_id)
    job = JobApplication(first_name=user.name,
                         last_name=user.second_name,
                         email=user.email,
                         phone_number=user.phone_number,
                         license_expired=context.user_data['expired_license'],
                         driver_license_front=context.user_data['front_license'],
                         driver_license_back=context.user_data['back_license'],
                         photo=context.user_data['photo_job'],
                         role=context.user_data['role'],
                         )
    if query and query.data == 'no_auto':
        query.edit_message_text(text=sms_text(user.phone_number))
        job.save()
    else:
        date = update.message.text
        if JobApplication.validate_date(date):
            job.insurance_expired = datetime.datetime.strptime(date, '%Y-%m-%d').date()
            job.car_documents = context.user_data['auto_doc']
            job.insurance = context.user_data['insurance']
            job.save()
            update.message.reply_text(text=sms_text(user.phone_number))
        else:
            update.message.reply_text(f'{date} {no_valid_insurance}')
            return 'WAIT_FOR_EXPIRED'
    context.user_data['thread'] = True
    t = threading.Thread(target=code_timer, args=(update, context, 180, 30), daemon=True)
    t.start()
    return "JOB_UKLON_CODE"


def uklon_code(update, context):
    chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    context.user_data['thread'] = False
    r = redis.Redis.from_url(os.environ["REDIS_URL"])
    r.publish(f'{user.phone_number} code', update.message.text)
    update.message.reply_text(accept_code_text)
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
                                             f'Залишилось {int(remaining_time)} секунд.'
                                             f'Якщо ви не відправите код заявку буде скасовано')
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


def save_storage_photo(image, filename):
    image_data = io.BytesIO()
    image.download(out=image_data)
    image_data.seek(0)
    storage_client = storage.Client(credentials=settings.GS_CREDENTIALS)
    bucket = storage_client.bucket(settings.GS_BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_file(image_data, content_type='image/jpeg')
