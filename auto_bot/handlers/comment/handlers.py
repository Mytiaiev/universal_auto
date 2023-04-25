from django.utils import timezone
from telegram import ReplyKeyboardRemove

from app.models import Order, Comment
from auto_bot.handlers.comment.keyboards import comment_keyboard
from auto_bot.handlers.main.keyboards import markup_keyboard
from auto_bot.handlers.order.static_text import COMMENT


def comment(update, context):
    context.user_data['state'] = COMMENT
    order = Order.get_order(chat_id_client=update.message.chat.id,
                            phone=context.user_data['phone_number'],
                            status_order=Order.WAITING)
    if order:
        order.status_order = Order.CANCELED
        order.save()
        update.message.reply_text('Поставте оцінку або напишіть відгук', reply_markup=markup_keyboard(comment_keyboard))
    else:
        update.message.reply_text('Залишіть відгук або сповістіть про проблему', reply_markup=ReplyKeyboardRemove())


def save_comment(update, context):
    order = Order.objects.filter(chat_id_client=update.message.chat.id,
                                 status_order=Order.CANCELED,
                                 created_at__date=timezone.now().date())
    user_comment = Comment.objects.create(
        comment=update.message.text,
        chat_id=update.message.chat.id)
    if order:
        last_order = list(order)[-1]
        last_order.comment = user_comment
        last_order.save()
    context.user_data['state'] = None
    update.message.reply_text("Ваш відгук було збережено. Очікуйте, менеджер скоро з вами зв`яжеться!")