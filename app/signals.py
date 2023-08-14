from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.utils import timezone

from auto.tasks import send_on_job_application_on_driver, check_time_order, setup_periodic_tasks, \
    remove_periodic_tasks, search_driver_for_order
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from app.models import Driver, StatusChange, JobApplication, ParkSettings, Partner, Order
from auto_bot.main import bot
from scripts.settings_for_park import settings_for_partner
from django.contrib.auth.models import User as AuUser
from scripts.google_calendar import create_event, datetime_with_timezone


@receiver(post_save, sender=AuUser)
def create_partner(sender, instance, created, **kwargs):
    if created:
        Partner.objects.create(user=instance)


@receiver(post_save, sender=Partner)
def create_park_settings(sender, instance, created, **kwargs):
    if created and not instance.user.is_superuser:
        setup_periodic_tasks(instance)
        for key in settings_for_partner.keys():
            response = settings_for_partner[key]
            ParkSettings.objects.create(key=key, value=response[0], description=response[1], partner=instance)


@receiver(post_delete, sender=AuUser)
def delete_park_settings(sender, instance, **kwargs):
    partner = Partner.objects.filter(user=instance)
    if partner:
        remove_periodic_tasks(partner.first())


@receiver(pre_save, sender=Driver)
def create_status_change(sender, instance, **kwargs):
    try:
        old_instance = Driver.objects.get(pk=instance.pk)
    except ObjectDoesNotExist:
        # new instance, ignore
        return
    if old_instance.driver_status != instance.driver_status:
        # update the end time of the previous status change
        prev_status_changes = StatusChange.objects.filter(driver=instance, end_time=None)
        prev_status_changes.update(end_time=timezone.now(), duration=F('end_time') - F('start_time'))
        if prev_status_changes.count() > 1:
            bot.send_message(chat_id=ParkSettings.get_value("DEVELOPER_CHAT_ID"),
                             text=f'Multiple status for driver {instance.id} deleted')
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


@receiver(post_save, sender=Order)
def take_order_from_client(sender, instance, **kwargs):
    if instance.status_order == Order.WAITING and not instance.checked:
        instance.checked = True
        instance.save()
        search_driver_for_order.delay(instance.pk)
    elif all([instance.status_order == Order.ON_TIME, instance.sum, not instance.checked]):
        check_time_order.delay(instance.pk)
        # g_id = ParkSettings.get_value("GOOGLE_ID_ORDER_CALENDAR")
        # if g_id:
        #     description = f"Адреса посадки: {instance.address}\n" \
        #                   f"Місце прибуття: {instance.to_address}\n" \
        #                   f"Спосіб оплати: {instance.payment}\n" \
        #                   f"Номер телефону: {instance.phone}\n"
        #     create_event(
        #         f"Замовлення {instance.pk}",
        #         description,
        #         datetime_with_timezone(instance.order_time),
        #         datetime_with_timezone(instance.order_time),
        #         ParkSettings.get_value("GOOGLE_ID_ORDER_CALENDAR")
        #     )

