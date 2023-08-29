# Generated by Django 4.1 on 2023-08-28 19:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0045_remove_order_report_tg_reporttelegrampayments_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='driver',
            name='worked',
            field=models.BooleanField(default=True, verbose_name='Працює'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='vehicle',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='app.vehicle', verbose_name='Автомобіль'),
        ),
    ]
