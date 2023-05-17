from django.utils import timezone
from telegram import ReplyKeyboardRemove

from app.models import Order, Comment, User
from auto_bot.handlers.comment.keyboards import comment_keyboard
from auto_bot.handlers.main.keyboards import markup_keyboard_onetime
from auto_bot.handlers.order.static_text import COMMENT


def comment(update, context):
    context.user_data['state'] = COMMENT
    try:
        query = update.callback_query
        chat_id = query.message.chat.id
    except:
        chat_id = update.message.chat.id
    user = User.get_by_chat_id(chat_id)
    order = Order.get_order(chat_id_client=chat_id,
                            phone=user.phone_number,
                            status_order=Order.WAITING)

    s_order = Order.objects.filter(chat_id_client=chat_id,
                                   phone_number=user.phone_number,
                                   status_order__in=[Order.IN_PROGRESS, Order.COMPLETED]).last()
    if any((order, s_order)):
        if order:
            order.status_order = Order.CANCELED
            order.save()
            update.message.reply_text('Поставте оцінку або напишіть відгук',
                                      reply_markup=markup_keyboard_onetime(comment_keyboard))
        else:
            context.bot.send_message(chat_id=chat_id, text='Поставте оцінку або напишіть відгук',
                                     reply_markup=markup_keyboard_onetime(comment_keyboard))
    else:
        update.message.reply_text('Залишіть відгук', reply_markup=ReplyKeyboardRemove())


def save_comment(update, context):
    order = Order.objects.filter(chat_id_client=update.message.chat.id,
                                 status_order__in=[Order.CANCELED, Order.COMPLETED],
                                 created_at__date=timezone.now().date()).last()
    user_comment = Comment.objects.create(
        comment=update.message.text,
        chat_id=update.message.chat.id)
    if order:
        order.comment = user_comment
        order.save()
    context.user_data['state'] = None
    update.message.reply_text("Ваш відгук було збережено. Очікуйте, менеджер скоро з вами зв`яжеться!")
