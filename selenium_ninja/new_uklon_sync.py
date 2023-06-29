from selenium_ninja.new_synchronizer import Synchronizer_V2
from django.db import IntegrityError
from app.models import Vehicle, Park, NewUklonPaymentsOrder, Partner, Service, ParkSettings


class Uklon(Synchronizer_V2):

    def get_header(self) -> dict:
        type_token, token = self.redis.get(f"{self.id}{self.variables[1]}"), self.redis.get(f"{self.id}{self.variables[0]}")

        headers = {
            'Authorization': f'{type_token.decode()} {token.decode()}'
         }
        return headers

    def park_payload(self) -> dict:
        payload = {
            'client_id': ParkSettings.get_value(key='CLIENT_ID', park=self.id),
            'client_secret': ParkSettings.get_value(key='CLIENT_SECRET', park=self.id),
            'contact': ParkSettings.get_value(key='UKLON_NAME', park=self.id),
            'device_id': "38c13dc5-2ef3-4637-99f5-8de26b2e8216",
            'grant_type': "password_mfa",
            'password': ParkSettings.get_value(key='UKLON_PASSWORD', park=self.id),
        }
        return payload

    def create_session(self):
        response = self.session.post(Service.get_value('UKLON_SESSION'), json=self.park_payload()).json()
        self.redis.set(f"{self.id}{self.variables[0]}", response["access_token"])
        self.redis.set(f"{self.id}{self.variables[1]}", response["token_type"])

    def response_data(self, url: str = None, params: dict = None,  pjson: dict = None) -> dict:
        if not self.redis.exists(f"{self.id}{self.variables[1]}") and self.redis.get(f"{self.id}{self.variables[0]}"):
            self.create_session()
        while True:
            response = self.session.get(
                url=url,
                headers=self.get_header(),
                json=pjson,
                params=params,
            )
            if response.status_code == '403':
                self.create_session()
            else:
                break
        return response.json()

    def to_float(self, number: int, div=100) -> float:
        return float("{:.2f}".format(number / div))

    def find_value(self, data: dict, *args) -> float:
        """Search value if args not False and return float"""
        nested_data = data

        for key in args:
            if key in nested_data:
                nested_data = nested_data[key]
            else:
                return float(0)

        return self.to_float(nested_data)

    def find_value_str(self, data: dict, *args) -> str:
        """Search value if args not False and return str"""
        nested_data = data

        for key in args:
            if key in nested_data:
                nested_data = nested_data[key]
            else:
                return ''

        return nested_data

    def create_report(self):
        start, end = str(self.start().int_timestamp), str(self.end().int_timestamp)
        param = self.parameters()
        param['dateFrom'], param['dateTo'] = start, end
        url = f"{Service.get_value('UKLON_3')}{ParkSettings.get_value(key='ID_PARK', park=self.id)}"
        url += Service.get_value('UKLON_4')
        data = self.response_data(url=url, params=param)['items']

        if data:
            for i in data:
                order = NewUklonPaymentsOrder(
                    report_from=start,
                    report_to=end,
                    report_file_name='',
                    full_name=f"{i['driver']['last_name']} {i['driver']['first_name']}",
                    signal=str(i['driver']['signal']),
                    total_rides=0 if 'total_orders_count' not in i else i['total_orders_count'],
                    total_distance=float(
                        0) if 'total_distance_meters' not in i else self.to_float(i['total_distance_meters'], div=1000),
                    total_amount_cach=self.find_value(i, *('profit', 'order', 'cash', 'amount')),
                    total_amount_cach_less=self.find_value(i, *('profit', 'order', 'wallet', 'amount')),
                    total_amount_on_card=self.find_value(i, *('profit', 'order', 'card', 'amount')),
                    total_amount=self.find_value(i, *('profit', 'order', 'total', 'amount')),
                    tips=self.find_value(i, *('profit', 'tips', 'amount')),
                    bonuses=float(0),
                    fares=float(0),
                    comission=self.find_value(i, *('loss', 'order', 'wallet', 'amount')),
                    total_amount_without_comission=self.find_value(i, *('profit', 'total', 'amount')),
                    partner=self.get_partner(),
                )
                try:
                    order.save()
                except IntegrityError:
                    pass
        else:
            order = NewUklonPaymentsOrder(
                report_from=start,
                report_to=end,
                report_file_name='',
                full_name='',
                signal='',
                total_rides=0,
                total_distance=0,
                total_amount_cach=0,
                total_amount_cach_less=0,
                total_amount_on_card=0,
                total_amount=0,
                tips=0,
                bonuses=0,
                fares=0,
                comission=0,
                total_amount_without_comission=0,
                partner=self.get_partner())
            try:
                order.save()
            except IntegrityError:
                pass

    def get_driver_status(self):
        first_key, second_key = 'width_client', 'wait'
        drivers = {
                first_key: [],
                second_key: [],
            }
        url = f"{Service.get_value('UKLON_5')}{ParkSettings.get_value(key='ID_PARK', park=self.id)}"
        url += Service.get_value('UKLON_6')
        data = self.response_data(url='url')

        for driver in data['drivers']:
            first_data = (driver['last_name'], driver['first_name'])
            second_data = (driver['first_name'], driver['last_name'])
            if driver['status'] == 'Active':
                drivers[f'{second_key}'].append(first_data)
                drivers[f'{second_key}'].append(second_data)
            elif driver['status'] == 'OrderExecution':
                drivers[f'{first_key}'].append(first_data)
                drivers[f'{first_key}'].append(second_data)

    def get_drivers(self):
        drivers = []
        param = self.parameters()
        param['name'], param['phone'], param['status'], param['limit'] = ('', '', 'All', '30')

        url = f"{Service.get_value('UKLON_1')}{ParkSettings.get_value(key='ID_PARK', park=self.id)}"
        url_1 = url + Service.get_value('UKLON_6')
        url_2 = url + Service.get_value('UKLON_2')

        all_drivers = self.session.get(url=url_1,params=param)

        for driver in all_drivers['items']:
            pay_cash, vehicle_name, vin_code = True, '', ''
            if driver['restrictions']:
                pay_cash = False if 'Cash' in driver['restrictions'][0]['restriction_types'] else True

            elif self.find_value_str(driver, *('selected_vehicle', )):
                vehicle_name = f"{driver['selected_vehicle']['make']} {driver['selected_vehicle']['model']}"
                vin_code = self.session.get(f"{url_2}/{driver['selected_vehicle']['vehicle_id']}")
                vin_code = vin_code.get('vin_code', '')

            email = self.session.get(f"{url_1}/{driver['id']}")

            drivers.append({
                'fleet_name': self.fleet,
                'name': driver['first_name'],
                'second_name': driver['last_name'],
                'email': email.get('email', ''),
                'phone_number': self.validate_phone_number(driver['phone']),
                'driver_external_id': driver['signal'],
                'pay_cash': pay_cash,
                'licence_plate': self.find_value_str(driver, *('selected_vehicle', 'license_plate')),
                'vehicle_name': vehicle_name.upper(),
                'vin_code': vin_code,
            })

        return drivers


u = Uklon()
u.get_drivers()