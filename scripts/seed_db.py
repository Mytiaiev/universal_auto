import random
from datetime import timedelta, datetime

from django.db import IntegrityError

from app.models import Driver, Vehicle, Fleets_drivers_vehicles_rate, BoltFleet, UberFleet, NewUklonFleet, \
    DriverRateLevels, NinjaFleet, SummaryReport, CarEfficiency

DRIVERS_MAP = {
    'fleets': [
        {'name': 'Uber', 'model': UberFleet, 'min_fee': 3000},
        {'name': 'Bolt', 'model': BoltFleet, 'min_fee': 4000},
        {'name': 'Uklon', 'model': NewUklonFleet, 'min_fee': 6000},
        {'name': 'Ninja', 'model': NinjaFleet, 'min_fee': 6000},
    ],
    'drivers': [
        {
            'name': 'Олександр',
            'second_name': 'Холін',
            'vehicle': {'licence_plate': 'AA3108YA', 'vin_code': 'LS6A2E0F1NA003113', 'name': '2022 Chang\'an Eado'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Uber', 'driver_external_id': '775f8943-b0ca-4079-90d3-c81d6563d0f1', 'rate': 0.50},
                    {'fleet': 'Bolt', 'driver_external_id': '+380661891408', 'rate': 0.50},
                    {'fleet': 'Uklon', 'driver_external_id': '512322', 'rate': 0.5},
                ]
        },
        {
            'name': 'Анатолій',
            'second_name': 'Мухін',
            'vehicle': {'licence_plate': 'KA4897BM', 'vin_code': 'VF1KZ140652639946', 'name': '2015 Renault Megane'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Uber', 'driver_external_id': '9a182345-fd18-490f-a908-94f520a9d2d1', 'rate': 0.6},
                    {'fleet': 'Bolt', 'driver_external_id': '+380936503350', 'rate': 0.6},
                    {'fleet': 'Uklon', 'driver_external_id': '519154', 'rate': 0.4},
                ]
        },
        {
            'name': 'Сергій',
            'second_name': 'Желамський',
            'vehicle': {'licence_plate': 'AA3107YA', 'vin_code': 'LS6A2E0F1NA089713', 'name': '2022 Chang\'an Eado'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Uber', 'driver_external_id': 'cd725b41-9e47-4fd0-8a1f-3514ddf6238a', 'rate': 0.50},
                    {'fleet': 'Bolt', 'driver_external_id': '+380668914200', 'rate': 0.50},
                    {'fleet': 'Uklon', 'driver_external_id': '512329', 'rate': 0.5},
                ]
        },
        {
            'name': 'Олег',
            'second_name': 'Філіппов',
            'vehicle': {'licence_plate': 'AA3410YA', 'vin_code': 'LC0CE4DC1N0090623', 'name': '2022 BYD E2'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Uber', 'driver_external_id': 'd303a6c5-56f7-4ebf-a341-9cfa7c759388', 'rate': 0.65},
                    {'fleet': 'Bolt', 'driver_external_id': '+380671887096', 'rate': 0.65},
                    {'fleet': 'Uklon', 'driver_external_id': '512875', 'rate': 0.35},
                ]
        },
        {
            'name': 'Юрій',
            'second_name': 'Філіппов',
            'vehicle': {'licence_plate': 'KA6041EI', 'vin_code': 'VF1RFB00X57177685', 'name': '2016 Renault Megane'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Uber', 'driver_external_id': '49dffc54-e8d9-47bd-a1e5-52ce16241cb6', 'rate': 0.65},
                    {'fleet': 'Bolt', 'driver_external_id': '+380502428878', 'rate': 0.65},
                    {'fleet': 'Uklon', 'driver_external_id': '512357', 'rate': 0.35},
                ]
        },
        {
            'name': 'Володимир',
            'second_name': 'Золотніков',
            'vehicle': {'licence_plate': 'KA4856BM', 'vin_code': 'VF1RFB00357090131', 'name': '2016 Renault Megane'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Uber', 'driver_external_id': '3b4ff5f9-ae59-465e-8e19-f00970963876', 'rate': 0.60},
                    {'fleet': 'Bolt', 'driver_external_id': '+380669692591', 'rate': 0.60},
                    {'fleet': 'Uklon', 'driver_external_id': '517489', 'rate': 0.4},
                ]
        },
        {
            'name': 'Євген',
            'second_name': 'Волонкович',
            'vehicle': {'licence_plate': 'KA8443EA', 'vin_code': 'VF1RFB00488090131', 'name': '2016 Renault Megane'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Bolt', 'driver_external_id': '+380937645871', 'rate': 0.65},
                ]
        },
        {
            'name': 'Максим',
            'second_name': 'Клочков',
            'vehicle': {'licence_plate': 'AA4314YA', 'vin_code': 'VF1RFB00352390131', 'name': '2016 Renault Megane'},
            'fleets_drivers_vehicles_rate':
                [

                    {'fleet': 'Uber', 'driver_external_id': 'fd19c311-523d-45fd-967f-b4c6408a9500', 'rate': 0.5},
                    {'fleet': 'Bolt', 'driver_external_id': '+380631694021', 'rate': 0.5},
                    {'fleet': 'Uklon', 'driver_external_id': '549340', 'rate': 0.5},
                ]
        },
    ],
    'driver_rate_levels': [
        {'fleet': 'Uber', 'threshold_value': 10500, 'rate_delta': -0.05},
        {'fleet': 'Uber', 'threshold_value': 9000, 'rate_delta': -0.05},
        {'fleet': 'Uber', 'threshold_value': 7000, 'rate_delta': -0.05},
        {'fleet': 'Bolt', 'threshold_value': 10500, 'rate_delta': -0.05},
        {'fleet': 'Bolt', 'threshold_value': 9000, 'rate_delta': -0.05},
        {'fleet': 'Bolt', 'threshold_value': 7000, 'rate_delta': -0.05},
        {'fleet': 'Uklon', 'threshold_value': 10500, 'rate_delta': -0.05},
        {'fleet': 'Uklon', 'threshold_value': 9000, 'rate_delta': -0.05},
        {'fleet': 'Uklon', 'threshold_value': 7000, 'rate_delta': -0.05},
        {'fleet': 'Uklon', 'threshold_value': 5000, 'rate_delta': -0.05},
        {'fleet': 'Uklon', 'threshold_value': 3000, 'rate_delta': -0.05},
    ],

}


def get_or_create_object(model, search_fields, **kwargs):
    try:
        print('+++++++++++++++++++++++++++++++++++++')
        print(kwargs)
        search_kwargs = {key: val for key, val in kwargs.items() if key in search_fields}
        obj = model.objects.get(**search_kwargs)
    except model.DoesNotExist:
        print('+++++++++++++++++++++++++++++++++++++')
        print(kwargs)
        obj = model.objects.create(**kwargs)
        print(f"--{model.__name__}--> {obj}")
    except IntegrityError:
        pass
    return obj


def init_models():
    fleets = {}
    for item in DRIVERS_MAP['fleets']:
        fleet = get_or_create_object(item['model'], ['name'], name=item['name'], min_fee=item['min_fee'])
        fleets[item['name']] = fleet

    for item in DRIVERS_MAP['drivers']:
        vehicle = get_or_create_object(Vehicle, ['licence_plate'],
                                       licence_plate=item['vehicle']['licence_plate'],
                                       vin_code=item['vehicle']['vin_code'],
                                       name=item['vehicle']['name'],

                                       )
        driver = get_or_create_object(Driver, ['name', 'second_name'],
                                      name=item['name'],
                                      second_name=item['second_name'],
                                      vehicle=vehicle
                                      )
        for rate in item['fleets_drivers_vehicles_rate']:
            print('+++++++++++++++++++++++++++++++++++++')
            print(driver)
            get_or_create_object(Fleets_drivers_vehicles_rate,
                                 ['fleet', 'driver'],
                                 fleet=fleets[rate['fleet']],
                                 driver=driver,
                                 vehicle=vehicle,
                                 driver_external_id=rate['driver_external_id'],
                                 )
    for item in DRIVERS_MAP['driver_rate_levels']:
        get_or_create_object(DriverRateLevels, ['fleet', 'threshold_value']
                             , fleet=fleets[item['fleet']]
                             , threshold_value=item['threshold_value']
                             , rate_delta=item['rate_delta']
                             )


def generate_random_amount(min_value, max_value):
    return round(random.uniform(min_value, max_value), 2)


def calculate_efficiency(total_amount, total_distance):
    if total_distance > 0:
        return round(total_amount / total_distance, 2)
    else:
        return 0


def generate_reports():
    today = datetime.now().date()

    drivers_data = DRIVERS_MAP['drivers']

    for driver_data in drivers_data:
        for i in range(7):
            report_from = today - timedelta(days=i)
            full_name = f"{driver_data['name']} {driver_data['second_name']}"
            total_amount_without_fee = generate_random_amount(500, 5000)
            total_amount_cash = generate_random_amount(50, 150)
            total_amount_on_card = round(total_amount_without_fee - total_amount_cash, 2)
            total_rides = random.randint(3, 10)
            total_distance = generate_random_amount(50, 250)
            fee = round((total_amount_cash + total_amount_on_card) * 0.15, 2)
            total_amount = round(total_amount_cash + total_amount_on_card + fee, 2)

            summary_report = get_or_create_object(
                SummaryReport,
                ['report_from', 'full_name'],
                report_from=report_from,
                full_name=full_name,
                total_amount_without_fee=total_amount_without_fee,
                total_amount_cash=total_amount_cash,
                total_amount_on_card=total_amount_on_card,
                total_amount=total_amount,
                total_rides=total_rides,
                total_distance=total_distance,
                fee=fee,
            )
            summary_report.save()


def update_car_efficiency():
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=7)

    summary_reports = SummaryReport.objects.filter(report_from__range=[seven_days_ago, today])

    for report in summary_reports:
        total_amount = report.total_amount
        total_distance = report.total_distance

        try:
            driver = Driver.objects.get(name=report.full_name.split()[0], second_name=report.full_name.split()[1])
            vehicle = driver.vehicle

        except Driver.DoesNotExist:
            vehicle = None

        efficiency = calculate_efficiency(total_amount, total_distance)

        car_efficiency, created = CarEfficiency.objects.get_or_create(
            report_from=report.report_from,
            vehicle=vehicle,
            defaults={
                'total_kasa': total_amount,
                'mileage': total_distance,
                'efficiency': efficiency,
            }
        )

        if not created:
            car_efficiency.total_kasa = total_amount
            car_efficiency.mileage = total_distance
            car_efficiency.efficiency = efficiency
            car_efficiency.save()


def run():
    init_models()
    generate_reports()
    update_car_efficiency()