# Generated by Django 4.1 on 2023-09-18 17:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0051_partner_chat_id_alter_driver_schema_alter_user_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='carefficiency',
            name='clean_kasa',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Чистий дохід'),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='manager',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.manager', verbose_name='Менеджер авто'),
        ),
    ]