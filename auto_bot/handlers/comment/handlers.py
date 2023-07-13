from django.utils import timezone

from app.models import Order, Comment
from auto_bot.handlers.comment.keyboards import inline_comment_kb, STAR
from auto_bot.handlers.order.static_text import COMMENT


def comment(update, context):
    query = update.callback_query
    order = Order.objects.filter(chat_id_client=query.message.chat_id,
                                 status_order__in=[Order.IN_PROGRESS, Order.WAITING, Order.COMPLETED],
                                 created_at__date=timezone.now().date()).last()
    if order:
        query.edit_message_text(text='Поставте оцінку або напишіть відгук')
        query.edit_message_reply_markup(reply_markup=inline_comment_kb())
        if order.status_order == Order.WAITING:
            order.status_order = Order.CANCELED
            order.save()
    else:
        query.edit_message_text(text='Напишіть відгук або пропозицію, будь ласка')
    context.user_data['state'] = COMMENT
    context.user_data['message_comment'] = query.message.message_id


def save_comment(update, context):
    query = update.callback_query
    text = "Ваш відгук було збережено"
    if query:
        query.edit_message_text(text=text)
        mark = int(query.data[0]) * STAR
    else:
        mark = update.message.text
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['message_comment'])
        context.bot.send_message(chat_id=update.effective_chat.id, text=text)
    order = Order.objects.filter(chat_id_client=update.effective_chat.id,
                                 status_order__in=[Order.CANCELED, Order.COMPLETED],
                                 created_at__date=timezone.now().date()).last()
    user_comment = Comment.objects.create(
        comment=mark,
        chat_id=update.effective_chat.id)
    order.comment = user_comment
    if order and order.driver:
        order.partner = order.driver.partner
    order.save()
    context.user_data['state'] = None
