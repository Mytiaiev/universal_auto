from django.utils import timezone

from app.models import Order, Comment
from auto_bot.handlers.comment.keyboards import inline_comment_kb
from auto_bot.handlers.comment.static_text import *
from auto_bot.handlers.order.static_text import COMMENT
from scripts.redis_conn import redis_instance
from auto_bot.handlers.main.keyboards import back_to_main_menu


def comment(update, context):
    query = update.callback_query
    order = Order.objects.filter(chat_id_client=query.message.chat_id,
                                 status_order__in=[Order.IN_PROGRESS, Order.WAITING, Order.COMPLETED],
                                 created_at__date=timezone.localtime().date()).last()
    if order:
        query.edit_message_text(mark_or_comment_text)
        query.edit_message_reply_markup(reply_markup=inline_comment_kb())
        if order.status_order == Order.WAITING:
            order.status_order = Order.CANCELED
            order.save()
    else:
        query.edit_message_text(no_order_comment_text)
    user_data = {'state': COMMENT, 'message_comment': query.message.message_id}
    redis_instance().hmset(str(update.effective_chat.id), user_data)


def save_comment(update, context):
    query = update.callback_query
    if query:
        query.edit_message_text(comment_save_text)
        query.edit_message_reply_markup(back_to_main_menu())
        mark = int(query.data[0]) * STAR
    else:
        message_id = redis_instance().hget(str(update.effective_chat.id), 'message_comment')
        mark = update.message.text
        context.bot.delete_message(chat_id=update.effective_chat.id, message_id=int(message_id))
        context.bot.send_message(chat_id=update.effective_chat.id, text=comment_save_text,
                                 reply_markup=back_to_main_menu())

    order = Order.objects.filter(chat_id_client=update.effective_chat.id,
                                 status_order__in=[Order.CANCELED, Order.COMPLETED],
                                 created_at__date=timezone.localtime().date()).last()
    user_comment = {"comment": mark,
                    "chat_id": update.effective_chat.id}
    comment_obj = Comment.objects.create(**user_comment)
    if order:
        if order.status_order == Order.COMPLETED:
            comment_obj.partner = order.partner
            comment_obj.save()
        order.comment = comment_obj
        order.save()
    redis_instance().hdel(str(update.effective_chat.id), 'state')
