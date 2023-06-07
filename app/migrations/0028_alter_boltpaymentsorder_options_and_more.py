# Generated by Django 4.1 on 2023-06-07 07:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0027_remove_driver_role_alter_client_role_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='boltpaymentsorder',
            options={'verbose_name': 'Платіжний звіт: Bolt', 'verbose_name_plural': 'Платіжні звіти: Bolt'},
        ),
        migrations.AlterModelOptions(
            name='fleets_drivers_vehicles_rate',
            options={'verbose_name': 'Рейтинг водія в автопарку', 'verbose_name_plural': 'Рейтинг водіїв в автопарках'},
        ),
        migrations.AlterModelOptions(
            name='newuklonpaymentsorder',
            options={'verbose_name': 'Платіжний звіт: NewUklon', 'verbose_name_plural': 'Платіжні звіти: NewUklon'},
        ),
        migrations.AlterModelOptions(
            name='ninjapaymentsorder',
            options={'verbose_name': 'Платіжний звіт: Ninja', 'verbose_name_plural': 'Платіжні звіти: Ninja'},
        ),
        migrations.AlterModelOptions(
            name='order',
            options={'verbose_name': 'Замовлення', 'verbose_name_plural': 'Замовлення'},
        ),
        migrations.AlterModelOptions(
            name='rentinformation',
            options={'verbose_name': 'Інформація по оренді', 'verbose_name_plural': 'Інформація по орендах'},
        ),
        migrations.AlterModelOptions(
            name='uberpaymentsorder',
            options={'verbose_name': 'Платіжний звіт: Uber', 'verbose_name_plural': 'Платіжні звіти: Uber'},
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='additional_fee',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Додатковий збір'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='autorization_deduction',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Авторизаційцний платіж (відрахування)'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='autorization_payment',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Авторизаційцний платіж (платіж)'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='cancels_amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Плата за скасування'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='compensation',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Компенсації'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Створено'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='discount_cash_trips',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Сума знижки Bolt за готівкові поїздки'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='driver_bonus',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Водійський бонус'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='driver_full_name',
            field=models.CharField(max_length=24, verbose_name='ПІ водія'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='fee',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Комісія Bolt'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='mobile_number',
            field=models.CharField(max_length=24, verbose_name='Унікальний індифікатор водія'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='partner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='range_string',
            field=models.CharField(max_length=50, verbose_name='Період'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='refunds',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Повернення коштів'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='report_file_name',
            field=models.CharField(max_length=255, verbose_name='Назва файлу'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='report_from',
            field=models.DateTimeField(verbose_name='Репорт з'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='report_to',
            field=models.DateTimeField(verbose_name='Репорт по'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='tips',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Чайові'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Загальний тариф'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='total_amount_cach',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Поїздки за готівку'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Оновлено'),
        ),
        migrations.AlterField(
            model_name='boltpaymentsorder',
            name='weekly_balance',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Тижневий баланс'),
        ),
        migrations.AlterField(
            model_name='driver',
            name='fleet',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.fleet', verbose_name='Автопарк'),
        ),
        migrations.AlterField(
            model_name='driver',
            name='partner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AlterField(
            model_name='drivermanager',
            name='partner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Створено'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='deleted_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Видалено'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='driver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.driver', verbose_name='Водій'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='driver_external_id',
            field=models.CharField(max_length=255, verbose_name='Унікальний індифікатор по автопарку'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='fleet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.fleet', verbose_name='Автопарк'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='partner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='pay_cash',
            field=models.BooleanField(default=False, verbose_name='Оплата готівкою'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='rate',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=3, verbose_name='Рейтинг'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Обновлено'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='vehicle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='app.vehicle', verbose_name='Автомобіль'),
        ),
        migrations.AlterField(
            model_name='fleets_drivers_vehicles_rate',
            name='withdraw_money',
            field=models.BooleanField(default=False, verbose_name='Зняття готівкі'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='bonuses',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Бонуси'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='comission',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Комісія Uklon'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Створено'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='fares',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Штрафи'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='full_name',
            field=models.CharField(max_length=255, verbose_name='ПІ водія'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='partner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='report_file_name',
            field=models.CharField(max_length=255, verbose_name='Назва файлу'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='report_from',
            field=models.DateTimeField(verbose_name='Репорт з'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='report_to',
            field=models.DateTimeField(verbose_name='Репорт по'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='signal',
            field=models.CharField(max_length=8, verbose_name='Унікальний індифікатор водія'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='tips',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Чайові'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Загальна сума'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='total_amount_cach',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Готівкою'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='total_amount_cach_less',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='На гаманець'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='total_amount_on_card',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='На картку'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='total_amount_without_comission',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Разом'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='total_distance',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Пробіг під замовлення'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='total_rides',
            field=models.PositiveIntegerField(verbose_name='Кількість поїздок'),
        ),
        migrations.AlterField(
            model_name='newuklonpaymentsorder',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Обновлено'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='chat_id',
            field=models.CharField(max_length=11, verbose_name='Унікальний індифікатор водія'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Створено'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='full_name',
            field=models.CharField(max_length=255, verbose_name='ПІ водія'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='partner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='report_from',
            field=models.DateTimeField(verbose_name='Репорт з'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='report_to',
            field=models.DateTimeField(verbose_name='Репорт по'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='total_amount',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Загальна сума'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='total_amount_cash',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Загальна сума готівкою'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='total_amount_on_card',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Загальна сума карточкою'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='total_distance',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Загальна дистанція'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='total_rides',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Кількість поїздок'),
        ),
        migrations.AlterField(
            model_name='ninjapaymentsorder',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Обновлено'),
        ),
        migrations.AlterField(
            model_name='order',
            name='car_delivery_price',
            field=models.CharField(blank=True, max_length=30, null=True, verbose_name='Сума за подачу автомобіля'),
        ),
        migrations.AlterField(
            model_name='order',
            name='chat_id_client',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Індифікатор чату клієнта'),
        ),
        migrations.AlterField(
            model_name='order',
            name='checked',
            field=models.BooleanField(default=False, verbose_name='Перевірено'),
        ),
        migrations.AlterField(
            model_name='order',
            name='client_message_id',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Індифікатор повідомлення клієнта'),
        ),
        migrations.AlterField(
            model_name='order',
            name='comment',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.comment', verbose_name='Відгук'),
        ),
        migrations.AlterField(
            model_name='order',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Cтворено'),
        ),
        migrations.AlterField(
            model_name='order',
            name='distance_google',
            field=models.CharField(max_length=10, verbose_name='Дистанція Google'),
        ),
        migrations.AlterField(
            model_name='order',
            name='distance_gps',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Дистанція по GPS'),
        ),
        migrations.AlterField(
            model_name='order',
            name='driver',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.RESTRICT, to='app.driver', verbose_name='Виконувач'),
        ),
        migrations.AlterField(
            model_name='order',
            name='driver_message_id',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Індифікатор повідомлення водія'),
        ),
        migrations.AlterField(
            model_name='order',
            name='from_address',
            field=models.CharField(max_length=255, verbose_name='Місце посадки'),
        ),
        migrations.AlterField(
            model_name='order',
            name='latitude',
            field=models.CharField(max_length=10, verbose_name='Широта місця посадки'),
        ),
        migrations.AlterField(
            model_name='order',
            name='longitude',
            field=models.CharField(max_length=10, verbose_name='Довгота місця посадки'),
        ),
        migrations.AlterField(
            model_name='order',
            name='partner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(max_length=70, verbose_name='Спосіб оплати'),
        ),
        migrations.AlterField(
            model_name='order',
            name='phone_number',
            field=models.CharField(max_length=13, verbose_name='Номер телефона клієнта'),
        ),
        migrations.AlterField(
            model_name='order',
            name='status_order',
            field=models.CharField(max_length=70, verbose_name='Статус замовлення'),
        ),
        migrations.AlterField(
            model_name='order',
            name='sum',
            field=models.CharField(max_length=30, verbose_name='Загальна сума'),
        ),
        migrations.AlterField(
            model_name='order',
            name='to_latitude',
            field=models.CharField(max_length=10, null=True, verbose_name='Широта місця висадки'),
        ),
        migrations.AlterField(
            model_name='order',
            name='to_longitude',
            field=models.CharField(max_length=10, null=True, verbose_name='Довгота місця висадки'),
        ),
        migrations.AlterField(
            model_name='order',
            name='to_the_address',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Місце висадки'),
        ),
        migrations.AlterField(
            model_name='rentinformation',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Створено'),
        ),
        migrations.AlterField(
            model_name='rentinformation',
            name='driver',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.driver', verbose_name='Водій'),
        ),
        migrations.AlterField(
            model_name='rentinformation',
            name='driver_name',
            field=models.CharField(blank=True, max_length=50, verbose_name='ПІ Водія'),
        ),
        migrations.AlterField(
            model_name='rentinformation',
            name='partner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Створено'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='driver_uuid',
            field=models.UUIDField(verbose_name='Унікальний індитифікатор водія'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='first_name',
            field=models.CharField(max_length=24, verbose_name='Імя водія'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='last_name',
            field=models.CharField(max_length=24, verbose_name='Прізвище водія'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='partner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.partner', verbose_name='Партнер'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='report_file_name',
            field=models.CharField(max_length=255, verbose_name='Назва файла'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='report_from',
            field=models.DateTimeField(verbose_name='Репорт з'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='report_to',
            field=models.DateTimeField(verbose_name='Репорт по'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='returns',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Відшкодування та витрати'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='tips',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Чайові'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='total_amount',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Загальна дохід'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='total_amount_cach',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Виплати'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='total_clean_amout',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Загальна дохід - Чистий тариф'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='transfered_to_bank',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Перераховано на банківський рахунок'),
        ),
        migrations.AlterField(
            model_name='uberpaymentsorder',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Обновлено'),
        ),
        migrations.AlterField(
            model_name='vehicle',
            name='partner',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='app.partner', verbose_name='Партнер'),
        ),
    ]
