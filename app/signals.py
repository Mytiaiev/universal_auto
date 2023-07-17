from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from auto.tasks import send_on_job_application_on_driver, check_order, check_time_order, selenium_session
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from app.models import Driver, Order, StatusChange, JobApplication, RentInformation, ParkSettings, ParkStatus, Partner
from auto_bot.main import bot
from scripts.settings_for_park import settings, settings_for_partner
from selenium import webdriver
from django.contrib.auth.models import User as AuUser
import os


@receiver(post_save, sender=AuUser)
def create_partner(sender, instance, created, **kwargs):
    if created:
        Partner.objects.create(user=instance)


@receiver(post_save, sender=Partner)
def create_park_settings(sender, instance, created, **kwargs):
    if created:
        driver = webdriver.Remote(command_executor=os.environ['SELENIUM_HUB_HOST'],
                                  desired_capabilities=webdriver.DesiredCapabilities.CHROME)
        selenium_session[instance.pk] = driver
        for key in settings_for_partner.keys():
            response = settings[key]
            ParkSettings.objects.create(key=key, value=response[0], description=response[1], partner=instance)


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
