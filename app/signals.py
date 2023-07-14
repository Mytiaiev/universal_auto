from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from auto.tasks import send_on_job_application_on_driver, check_order, check_time_order
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from app.models import Driver, Order, StatusChange, JobApplication, RentInformation, ParkSettings, ParkStatus,  Park, \
    Partner
from auto_bot.main import bot
from scripts.redis_conn import redis_instance
from scripts.settings_for_park import settings
from django.contrib.auth.models import User as AuUser


@receiver(post_save, sender=AuUser)
def create_partner(sender, instance, created, **kwargs):
    if created:
        Partner.objects.create(user=instance)


@receiver(post_save, sender=Park)
def create_park_settings(sender, instance, created, **kwargs):
    if created:
        keys_to_save = ('UBER_NAME', 'UBER_PASSWORD',
                        'BOLT_NAME', 'BOLT_PASSWORD',
                        'UKLON_NAME', 'UKLON_PASSWORD',
                        'UKLON_TOKEN', 'DRIVERS_CHAT',
                        'ID_PARK', 'CLIENT_ID',
                        'CLIENT_SECRET')

        for key in keys_to_save:
            response = settings[key]
            ParkSettings.objects.create(key=key, value=response[0], description=response[1], park=instance)


@receiver(pre_save, sender=Driver)
def create_status_change(sender, instance, **kwargs):
    try:
        old_instance = Driver.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        # new instance, ignore
        return
    if old_instance.driver_status != instance.driver_status:
        # update the end time of the previous status change
        prev_status_change = StatusChange.objects.filter(driver=instance, end_time=None).first()
        if prev_status_change:
            prev_status_change.end_time = timezone.now()
            prev_status_change.duration = prev_status_change.end_time - prev_status_change.start_time
            prev_status_change.save()
        # driver_status has changed, create new status change
        status_change = StatusChange(
            driver=instance,
            name=instance.driver_status,
            vehicle=instance.vehicle,
            start_time=timezone.now(),
        )
        status_change.save()


@receiver(post_save, sender=JobApplication)
def run_add_drivers_task(sender, instance, created, **kwargs):
    if created:
        send_on_job_application_on_driver.delay(instance.id)


# @receiver(post_save, sender=RentInformation)
# def send_day_rent(sender, instance, **kwargs):
#     try:
#         chat_id = instance.driver.chat_id
#         # if instance.rent_distance > 20 and instance.driver.driver_status != Driver.OFFLINE:
#         #     rent_cost = int((instance.rent_distance-ParkSettings.get_value('FREE_RENT', 20))*ParkSettings.get_value('RENT_PRICE', 15))
#         #     message = f"""Ваша оренда сьогодні {instance.rent_distance} км,
#         #      вартість оренди {rent_cost}грн"""
#         #     bot.send_message(chat_id=chat_id, text=message)
#     except:
#         pass


@receiver(post_save, sender=Order)
def take_order_from_client(sender, instance, **kwargs):
    if instance.status_order == Order.WAITING and not instance.checked:
        check_order.delay(instance.id)
    elif all([instance.status_order == Order.ON_TIME, instance.sum, not instance.checked]):
        check_time_order.delay(instance.id)


@receiver(pre_save, sender=Order)
def reject_order_client(sender, instance, **kwargs):

    if instance.status_order == Order.CANCELED:
        try:
            driver_chat_id = instance.driver.chat_id
            driver = Driver.get_by_chat_id(chat_id=driver_chat_id)
            message_id = instance.driver_message_id
            bot.delete_message(chat_id=driver_chat_id, message_id=message_id)
            bot.send_message(
                chat_id=driver_chat_id,
                text=f'Вибачте, замовлення за адресою {instance.from_address} відхилено клієнтом.'
            )
            ParkStatus.objects.create(driver=driver, status=Driver.ACTIVE)
        except Exception:
            pass
