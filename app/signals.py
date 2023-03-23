from django.db.models.signals import post_save
from django.dispatch import receiver
from auto.tasks import send_on_job_application_on_driver_to_Bolt, send_on_job_application_on_driver_to_NewUklon
from app.models import JobApplication

@receiver(post_save, sender=JobApplication)
def run_uklon_task(sender, instance, created, **kwargs):
    if created:
        send_on_job_application_on_driver_to_NewUklon.delay(instance.id)

# @receiver(post_save, sender=JobApplication)
# def run_bolt_task(sender, instance, created, **kwargs):
#     if created:
#         send_on_job_application_on_driver_to_Bolt.delay(instance.id)
