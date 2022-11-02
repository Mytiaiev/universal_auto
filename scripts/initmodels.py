from app.models import Driver, Vehicle, Fleets_drivers_vehicles_rate, BoltFleet, UberFleet, UklonFleet, NewUklonFleet

DRIVERS_MAP = {
    'fleets': [
        {'name': 'Uber', 'model': UberFleet},
        {'name': 'Bolt', 'model': BoltFleet},
        {'name': 'Uklon', 'model': UklonFleet},
        {'name': 'NewUklon', 'model': NewUklonFleet},
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
                    {'fleet': 'Uklon', 'driver_external_id': '372353', 'rate': 0.50},
                    {'fleet': 'NewUklon', 'driver_external_id': '512322', 'rate': 0.35},
                ]
        },
        {
            'name': 'Анатолій',
            'second_name': 'Мухін',
            'vehicle': {'licence_plate': 'KA4897BM', 'vin_code': 'VF1KZ140652639946', 'name': '2015 Renault Megane'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Uber', 'driver_external_id': '9a182345-fd18-490f-a908-94f520a9d2d1', 'rate': 0.65},
                    {'fleet': 'Bolt', 'driver_external_id': '+380936503350', 'rate': 0.65},
                    {'fleet': 'Uklon', 'driver_external_id': '362612', 'rate': 0.35},
                    {'fleet': 'NewUklon', 'driver_external_id': '519154', 'rate': 0.35},
                ]
        },
        {
            'name': 'Сергій',
            'second_name': 'Желамський',
            'vehicle': {'licence_plate': 'AA3107YA', 'vin_code': 'LS6A2E0F1NA003113', 'name': '2022 Chang\'an Eado'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Uber', 'driver_external_id': 'cd725b41-9e47-4fd0-8a1f-3514ddf6238a', 'rate': 0.50},
                    {'fleet': 'Bolt', 'driver_external_id': '+380668914200', 'rate': 0.50},
                    {'fleet': 'Uklon', 'driver_external_id': '372350', 'rate': 0.50},
                    {'fleet': 'NewUklon', 'driver_external_id': '512329', 'rate': 0.35},
                ]
        },
        {
            'name': 'Олег',
            'second_name': 'Філіппов',
            'vehicle': {'licence_plate': 'AA3410YA', 'vin_code': 'LC0CE4DC1N0090623', 'name': '2022 BYD E2'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Uber', 'driver_external_id': 'd303a6c5-56f7-4ebf-a341-9cfa7c759388', 'rate': 0.60},
                    {'fleet': 'Bolt', 'driver_external_id': '+380671887096', 'rate': 0.60},
                    {'fleet': 'Uklon', 'driver_external_id': '324460', 'rate': 0.40},
                    {'fleet': 'NewUklon', 'driver_external_id': '512875', 'rate': 0.35},
                ]
        },
        {
            'name': 'Юрій',
            'second_name': 'Філіппов',
            'vehicle': {'licence_plate': 'KA8443EA', 'vin_code': 'VF1RFB00X57177685', 'name': '2016 Renault Megane'},
            'fleets_drivers_vehicles_rate':
                [
                    {'fleet': 'Uber', 'driver_external_id': '49dffc54-e8d9-47bd-a1e5-52ce16241cb6', 'rate': 0.65},
                    {'fleet': 'Bolt', 'driver_external_id': '+380502428878', 'rate': 0.65},
                    {'fleet': 'Uklon', 'driver_external_id': '357339', 'rate': 0.35},
                    {'fleet': 'NewUklon', 'driver_external_id': '512357', 'rate': 0.35},
                ]
        },
        {
            'name': 'Володимир',
            'second_name': 'Золотніков',
            'vehicle': {'licence_plate': 'KA1644CT', 'vin_code': 'VF1RFB00357090131', 'name': '2016 Renault Megane'},
            'fleets_drivers_vehicles_rate':
                [   
                    {'fleet': 'Uber', 'driver_external_id': '3b4ff5f9-ae59-465e-8e19-f00970963876', 'rate': 0.65},
                    {'fleet': 'Bolt', 'driver_external_id': '+380669692591', 'rate': 0.65},
                    {'fleet': 'Uklon', 'driver_external_id': '368808', 'rate': 0.35},
                    {'fleet': 'NewUklon', 'driver_external_id': '517489', 'rate': 0.35},
                ]
        },

    ],
}


def get_or_create_object(model, search_fields, **kwargs):
    try:
        search_kwargs = {key: val for key, val in kwargs.items() if key in search_fields}
        obj = model.objects.get(**search_kwargs)
    except model.DoesNotExist:
        obj = model.objects.create(**kwargs)
        print(f"--{model.__name__}--> {obj}")
    return obj


def init_models():
    fleets = {}
    for item in DRIVERS_MAP['fleets']:
        fleet = get_or_create_object(item['model'], ['name'], name=item['name'])
        fleets[item['name']] = fleet

    for item in DRIVERS_MAP['drivers']:
        driver = get_or_create_object(Driver, ['name', 'second_name'], name=item['name'], second_name=item['second_name'])
        vehicle = get_or_create_object(Vehicle, ['licence_plate', 'vin_code'],
                                       licence_plate=item['vehicle']['licence_plate'],
                                       vin_code=item['vehicle']['vin_code'],
                                       name=item['vehicle']['name']
                                       )
        for rate in item['fleets_drivers_vehicles_rate']:
            get_or_create_object(Fleets_drivers_vehicles_rate,
                                 ['fleet', 'driver', 'vehicle'],
                                 fleet=fleets[rate['fleet']],
                                 driver=driver,
                                 vehicle=vehicle,
                                 driver_external_id=rate['driver_external_id'],
                                 rate=rate['rate']
                                 )


def run():
    init_models()
