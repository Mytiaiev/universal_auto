from django.utils import timezone
from auto.tasks import send_on_job_application_on_driver_to_Bolt, send_on_job_application_on_driver_to_NewUklon
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from app.models import Driver, StatusChange, JobApplication


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
        send_on_job_application_on_driver_to_NewUklon.delay(instance.id)
        send_on_job_application_on_driver_to_Bolt.delay(instance.id)
