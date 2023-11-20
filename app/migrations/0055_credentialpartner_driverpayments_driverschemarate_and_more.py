# Generated by Django 4.1 on 2023-10-04 12:23

import app.models
from django.db import migrations, models
import django.db.models.deletion

def update_schema_references(apps, schema_editor):
    Driver = apps.get_model('app', 'Driver')
    Schema = apps.get_model('app', 'Schema')
    schema_list = [('HALF', 'Схема 50/50'), ('CUSTOM', 'Індивідуальний відсоток'),
                   ('DYNAMIC', 'Динамічна схема'), ('RENT', 'Схема оренди')]
    for schema, title in schema_list:
        fk_schema, _ = Schema.objects.get_or_create(title=title, schema=schema)
        Driver.objects.filter(schema=schema).update(schema=str(fk_schema.id))


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0054_transactionsconversation_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CredentialPartner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=255, verbose_name='Ключ')),
                ('value', models.BinaryField(verbose_name='Значення')),
            ],
        ),
        migrations.CreateModel(
            name='DriverPayments',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_from', models.DateField(verbose_name='Звіт з')),
                ('report_to', models.DateField(verbose_name='Звіт по')),
                ('report_type', models.CharField(choices=[('WEEK', 'Тижневий'), ('DAY', 'Денний')], max_length=25, verbose_name='Тип звіту')),
                ('kasa', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Заробіток за період')),
                ('cash', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Готівка')),
                ('rent_distance', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Орендована дистанція')),
                ('rent', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Оренда авто')),
                ('salary', models.DecimalField(decimal_places=2, default=0, max_digits=10, verbose_name='Виплачено водію')),
            ],
            options={
                'verbose_name': 'Виплати водію',
                'verbose_name_plural': 'Виплати водіям',
            },
        ),
        migrations.CreateModel(
            name='DriverSchemaRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('period', models.CharField(choices=[('WEEK', 'Тижневий'), ('DAY', 'Денний')], max_length=25, verbose_name='Період розрахунку')),
                ('threshold', models.DecimalField(decimal_places=2, default=0, max_digits=15, verbose_name='Поріг доходу')),
                ('rate', models.DecimalField(decimal_places=2, default=0, max_digits=3, verbose_name='Відсоток')),
            ],
            options={
                'verbose_name': 'Тариф водія',
                'verbose_name_plural': 'Тарифи водія',
            },
        ),
        migrations.CreateModel(
            name='Schema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='Назва схеми')),
                ('schema', models.CharField(choices=[('RENT', 'Схема оренди'), ('HALF', 'Схема 50/50'), ('DYNAMIC', 'Динамічна схема'), ('CUSTOM', 'Індивідуальний відсоток')], default=('HALF', 'Схема 50/50'), max_length=25, verbose_name='Шаблон схеми')),
                ('plan', models.IntegerField(default=12000, verbose_name='План водія')),
                ('rental', models.IntegerField(default=6000, verbose_name='Вартість прокату')),
                ('rate', models.DecimalField(decimal_places=2, default=0.5, max_digits=3, verbose_name='Відсоток водія')),
            ],
            options={
                'verbose_name': 'Схему роботи',
                'verbose_name_plural': 'Схеми роботи',
            },
        ),
        migrations.AlterModelOptions(
            name='fleetorder',
            options={'verbose_name': 'Замовлення в агрегаторах', 'verbose_name_plural': 'Замовлення в агрегаторах'},
        ),
        migrations.RemoveField(
            model_name='driver',
            name='plan',
        ),
        migrations.RemoveField(
            model_name='driver',
            name='rate',
        ),
        migrations.RemoveField(
            model_name='driver',
            name='rental',
        ),
        migrations.AddField(
            model_name='driver',
            name='salary_calculation',
            field=models.CharField(choices=[('WEEK', 'Тижневий'), ('DAY', 'Денний')], default='WEEK', max_length=25, verbose_name='Період розрахунку зарплати'),
        ),
        migrations.AlterField(
            model_name='investor',
            name='role',
            field=models.CharField(choices=[('CLIENT', 'Клієнт'), ('DRIVER', 'Водій'), ('DRIVER_MANAGER', 'Менеджер водіїв'), ('SERVICE_STATION_MANAGER', 'Сервісний менеджер'), ('SUPPORT_MANAGER', 'Менеджер підтримки'), ('OWNER', 'Власник'), ('INVESTOR', 'Інвестор')], default='INVESTOR', max_length=25),
        ),
        migrations.AlterField(
            model_name='manager',
            name='role',
            field=models.CharField(choices=[('CLIENT', 'Клієнт'), ('DRIVER', 'Водій'), ('DRIVER_MANAGER', 'Менеджер водіїв'), ('SERVICE_STATION_MANAGER', 'Сервісний менеджер'), ('SUPPORT_MANAGER', 'Менеджер підтримки'), ('OWNER', 'Власник'), ('INVESTOR', 'Інвестор')], default='DRIVER_MANAGER', max_length=25),
        ),
        migrations.AlterField(
            model_name='partner',
            name='role',
            field=models.CharField(choices=[('CLIENT', 'Клієнт'), ('DRIVER', 'Водій'), ('DRIVER_MANAGER', 'Менеджер водіїв'), ('SERVICE_STATION_MANAGER', 'Сервісний менеджер'), ('SUPPORT_MANAGER', 'Менеджер підтримки'), ('OWNER', 'Власник'), ('INVESTOR', 'Інвестор')], default='OWNER', max_length=25),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('CLIENT', 'Клієнт'), ('DRIVER', 'Водій'), ('DRIVER_MANAGER', 'Менеджер водіїв'), ('SERVICE_STATION_MANAGER', 'Сервісний менеджер'), ('SUPPORT_MANAGER', 'Менеджер підтримки'), ('OWNER', 'Власник'), ('INVESTOR', 'Інвестор')], default='CLIENT', max_length=25),
        ),
        migrations.DeleteModel(
            name='DriverRateLevels',
        ),
        migrations.AddField(
            model_name='schema',
            name='partner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AddField(
            model_name='driverschemarate',
            name='partner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AddField(
            model_name='driverpayments',
            name='driver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.driver', verbose_name='Водій'),
        ),
        migrations.AddField(
            model_name='driverpayments',
            name='partner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AddField(
            model_name='credentialpartner',
            name='partner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.RunPython(update_schema_references),
        migrations.AlterField(
            model_name='driver',
            name='schema',
            field=models.ForeignKey(default=app.models.Schema.get_half_schema_id, on_delete=django.db.models.deletion.CASCADE, to='app.schema', verbose_name='Схема роботи'),
        ),
    ]
