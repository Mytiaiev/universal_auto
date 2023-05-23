from django.utils import timezone
from telegram import ReplyKeyboardRemove

from app.models import Order, Comment, User
from auto_bot.handlers.comment.keyboards import inline_comment_kb, STAR
from auto_bot.handlers.main.keyboards import markup_keyboard_onetime
from auto_bot.handlers.order.static_text import COMMENT


def comment(update, context):
    context.user_data['state'] = COMMENT
    query = update.callback_query
    chat_id = query.message.chat.id
    order = Order.objects.filter(chat_id_client=chat_id,
                                 status_order__in=[Order.IN_PROGRESS, Order.WAITING, Order.COMPLETED]).last()
    if order:
        if order.status_order == Order.WAITING:
            order.status_order = Order.CANCELED
            order.save()
    context.bot.send_message(chat_id=chat_id, text='Поставте оцінку або напишіть відгук',
                             reply_markup=inline_comment_kb())


def save_comment(update, context):
    query = update.callback_query
    if query:
        mark = int(query.data[0]) * STAR
    else:
        mark = update.message.text
    order = Order.objects.filter(chat_id_client=update.effective_chat.id,
                                 status_order__in=[Order.CANCELED, Order.COMPLETED],
                                 created_at__date=timezone.now().date()).last()
    user_comment = Comment.objects.create(
        comment=mark,
        chat_id=update.effective_chat.id)
    if order:
        order.comment = user_comment
        order.save()
    context.user_data['state'] = None
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ваш відгук було збережено")
