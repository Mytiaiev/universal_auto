from django.utils import timezone
from auto.tasks import send_on_job_application_on_driver
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from app.models import Driver, StatusChange, JobApplication, RentInformation, ParkSettings
from auto_bot.main import bot


@receiver(pre_save, sender=Driver)
def create_status_change(sender, instance, **kwargs):
    try:
        old_instance = Driver.objects.get(pk=instance.pk)
    except Driver.DoesNotExist:
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
            start_time=timezone.now(),
        )
        status_change.save()


@receiver(post_save, sender=JobApplication)
def run_add_drivers_task(sender, instance, created, **kwargs):
    if created:
        send_on_job_application_on_driver.delay(instance.id)


@receiver(post_save, sender=RentInformation)
def send_day_rent(sender, instance, **kwargs):
    try:
        chat_id = instance.driver.chat_id
        if instance.rent_distance > 20 and instance.driver.driver_status != Driver.OFFLINE:
            rent_cost = int((instance.rent_distance-ParkSettings.get_value('FREE_RENT', 20))*ParkSettings.get_value('RENT_PRICE', 15))
            message = f"""Ваша оренда сьогодні {instance.rent_distance} км,
             вартість оренди {rent_cost}грн"""
            bot.send_message(chat_id=chat_id, text=message)
    except:
        pass
