import json
from datetime import timedelta

from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import authenticate, login

from app.models import *
from selenium_ninja.driver import SeleniumTools


def active_vehicles_gps():
	vehicles_gps = []
	active_drivers = Driver.objects.filter(driver_status=Driver.ACTIVE)
	for driver in active_drivers:
		today = date.today()
		vehicle = UseOfCars.objects.filter(user_vehicle=driver,
										   created_at__date=today).first()
		if vehicle:
			vehicles = VehicleGPS.objects.filter(
				vehicle__licence_plate=vehicle.licence_plate
			).values('vehicle__licence_plate', 'lat', 'lon').last()
			vehicles_gps.append(vehicles)
	json_data = json.dumps(vehicles_gps, cls=DjangoJSONEncoder)
	return json_data


def order_confirm(id_order):
	order = Order.objects.get(id=id_order)
	car_delivery_price = order.car_delivery_price
	driver = order.driver
	vehicle = UseOfCars.objects.filter(user_vehicle=driver).first()
	if vehicle is not None:
		vehicle_gps = VehicleGPS.objects.filter(
			vehicle__licence_plate=vehicle.licence_plate
		).values('vehicle__licence_plate', 'lat', 'lon')
		data = {
			'vehicle_gps': list(vehicle_gps),
			'car_delivery_price': car_delivery_price
		}
		json_data = json.dumps(data, cls=DjangoJSONEncoder)
		return json_data
	else:
		return "[]"


def update_order_sum_or_status(id_order, action):
	if action == 'user_opt_out':
		order = Order.objects.get(id=id_order)
		order.status_order = Order.CANCELED
		order.save()


def restart_order(id_order, car_delivery_price, action):
	if action == 'increase_price':
		order = Order.objects.get(id=id_order)
		order.car_delivery_price = car_delivery_price
		order.checked = False
		order.save()

	if action == 'continue_search':
		order = Order.objects.get(id=id_order)
		order.checked = False
		order.save()


# Робота з dashboard.html #################


def get_dates(period=None):
	if period == 'day':
		current_date = timezone.now().date()
		previous_date = current_date - timedelta(days=1)

		start_date = previous_date
		end_date = current_date
		return start_date, end_date

	elif period == 'week':
		current_date = timezone.now().date()
		weekday = current_date.weekday()

		if weekday == 0:
			start_date = current_date - timedelta(days=7)
			end_date = start_date + timedelta(days=6)
		else:
			start_date = current_date - timedelta(days=weekday)
			end_date = start_date + timedelta(days=6)
		return start_date, end_date

	elif period == 'month':
		current_date = timezone.now().date()
		start_date = current_date.replace(day=1)
		next_month = current_date.replace(day=28) + timedelta(days=4)
		end_date = next_month - timedelta(days=next_month.day)
		return start_date, end_date

	elif period == 'quarter':
		current_date = timezone.now().date()
		current_month = current_date.month
		current_quarter = (current_month - 1) // 3 + 1

		if current_quarter == 1:
			start_date = date(current_date.year, 1, 1)
			end_date = date(current_date.year, 3, 31)
			return start_date, end_date
		elif current_quarter == 2:
			start_date = date(current_date.year, 4, 1)
			end_date = date(current_date.year, 6, 30)
			return start_date, end_date
		elif current_quarter == 3:
			start_date = date(current_date.year, 7, 1)
			end_date = date(current_date.year, 9, 30)
			return start_date, end_date
		elif current_quarter == 4:
			start_date = date(current_date.year, 10, 1)
			end_date = date(current_date.year, 12, 31)
			return start_date, end_date
	else:
		current_date = timezone.now().date()
		weekday = current_date.weekday()

		if weekday == 0:
			start_date = current_date - timedelta(days=7)
			end_date = start_date + timedelta(days=6)
		else:
			start_date = current_date - timedelta(days=weekday)
			end_date = start_date + timedelta(days=6)
		return start_date, end_date


def weekly_rent():
	week_start, week_end = get_dates('week')

	start_date_formatted = week_start.strftime('%d.%m.%Y')
	end_date_formatted = week_end.strftime('%d.%m.%Y')

	total_distance = RentInformation.objects.filter(
		created_at__date__range=(week_start, week_end)).aggregate(
		total_distance=Sum('rent_distance'))['total_distance'] or 0

	return total_distance, start_date_formatted, end_date_formatted


def collect_total_earnings(period):
	total = {}
	total_amount = 0

	start_period, end_period = get_dates(period)
	start_date_formatted = start_period.strftime('%d.%m.%Y')
	end_date_formatted = end_period.strftime('%d.%m.%Y')

	reports = SummaryReport.objects.filter(
		report_from__range=(start_period, end_period))
	for driver in Driver.objects.all():
		total[driver.full_name()] = reports.filter(full_name=driver).aggregate(
			clean_kasa=Sum('total_amount_without_fee'))['clean_kasa']
		if total.get(driver.full_name()):
			total_amount += total[driver.full_name()]
	return total, total_amount, start_date_formatted, end_date_formatted


def average_effective_vehicle():
	start_date, end_date = get_dates('week')

	start_date_formatted = start_date.strftime('%d.%m.%Y')
	end_date_formatted = end_date.strftime('%d.%m.%Y')

	vehicle = CarEfficiency.objects.filter(
		report_from__range=(start_date, end_date))
	effective = 0
	if vehicle:
		mileage = vehicle.aggregate(Sum('mileage'))['mileage__sum'] or 0
		total_kasa = vehicle.aggregate(Sum('total_kasa'))[
						 'total_kasa__sum'] or 0
		effective = total_kasa / mileage
		effective = float('{:.2f}'.format(effective))

	return effective, start_date_formatted, end_date_formatted


def effective_vehicle(period, vehicle):
	start_date, end_date = get_dates(period=period)
	car_effective = []

	effective_objects = CarEfficiency.objects.filter(
		licence_plate=vehicle,
		report_from__range=(start_date, end_date)).order_by('report_from')

	for effective in effective_objects:
		date_effective = effective.report_from
		name = effective.driver
		total_amount = effective.total_kasa
		car = effective.licence_plate
		mileage = effective.mileage
		effective = effective.efficiency

		car_data = {
			'date_effective': date_effective,
			'car': car,
			'name': name,
			'total_amount': total_amount,
			'mileage': mileage,
			'effective': effective
		}
		car_effective.append(car_data)
	result = {'data': car_effective}

	return result


def login_in(action, login_name, password, user_id):
	partner = Partner.objects.get(user_id=user_id)
	selenium_tools = SeleniumTools(partner=partner.pk)
	if action == 'Bolt_login':
		success_login = selenium_tools.bolt_login(login=login_name,
												  password=password)

		if success_login[0]:
			bolt_url_id = success_login[1].split('/')[-2]
			try:
				bolt_password_setting = ParkSettings.objects.get(
					key='BOLT_PASSWORD', partner=partner)
				if bolt_password_setting.value != password:
					bolt_password_setting.value = password
					bolt_password_setting.save()
			except ParkSettings.DoesNotExist:
				ParkSettings.objects.create(key='BOLT_PASSWORD', value=password,
											partner=partner)

			try:
				bolt_name_setting = ParkSettings.objects.get(key='BOLT_NAME',
															 partner=partner)
				if bolt_name_setting.value != login_name:
					bolt_name_setting.value = login_name
					bolt_name_setting.save()
			except ParkSettings.DoesNotExist:
				ParkSettings.objects.create(key='BOLT_NAME', value=login_name,
											partner=partner)

			try:
				bolt_url_setting = ParkSettings.objects.get(
					key='BOLT_URL_ID_PARK', partner=partner)
				if bolt_url_setting.value != bolt_url_id:
					bolt_url_setting.value = bolt_url_id
					bolt_url_setting.save()
			except ParkSettings.DoesNotExist:
				ParkSettings.objects.create(key='BOLT_URL_ID_PARK',
											value=bolt_url_id,
											description='BOLT_URL_ID_Парка',
											partner=partner)

			return True
		else:
			return False

	if action == 'Uklon_login':
		success_login = selenium_tools.uklon_login(login=login_name[4:],
												   password=password)
		if success_login:
			try:
				uklon_password_setting = ParkSettings.objects.get(
					key='UKLON_PASSWORD', partner=partner)
				if uklon_password_setting.value != password:
					uklon_password_setting.value = password
					uklon_password_setting.save()
			except ParkSettings.DoesNotExist:
				ParkSettings.objects.create(key='UKLON_PASSWORD',
											value=password, partner=partner)

			try:
				uklon_name_setting = ParkSettings.objects.get(key='UKLON_NAME',
															  partner=partner)
				if uklon_name_setting.value != login_name:
					uklon_name_setting.value = login_name
					uklon_name_setting.save()
			except ParkSettings.DoesNotExist:
				ParkSettings.objects.create(key='UKLON_NAME', value=login_name,
											partner=partner)

			return True
		else:
			return False

	if action == 'Uber_login':
		success_login = selenium_tools.uber_login(login=login_name,
												  password=password)
		if success_login:
			try:
				uber_password_setting = ParkSettings.objects.get(
					key='UBER_PASSWORD', partner=partner)
				if uber_password_setting.value != password:
					uber_password_setting.value = password
					uber_password_setting.save()
			except ParkSettings.DoesNotExist:
				ParkSettings.objects.create(key='UBER_PASSWORD', value=password,
											partner=partner)

			try:
				uber_name_setting = ParkSettings.objects.get(key='UBER_NAME',
															 partner=partner)
				if uber_name_setting.value != login_name:
					uber_name_setting.value = login_name
					uber_name_setting.save()
			except ParkSettings.DoesNotExist:
				ParkSettings.objects.create(key='UBER_NAME', value=login_name,
											partner=partner)

			return True
		else:
			return False


def login_in_investor(request, login_name, password):
	user = authenticate(username=login_name, password=password)
	if user is not None:
		if user.is_active:
			login(request, user)
			user_name = user.get_username()

			return {'success': True, 'user_name': user_name}
		else:
			return {'success': False, 'message': 'User is not active'}
	else:
		return {'success': False, 'message': 'User is not found'}


def change_password_investor(request, login, password, new_password):
	user = authenticate(username=login, password=password)
	if user is not None:
		if user.is_active:
			user.set_password(new_password)
			user.save()
			return {'success': True}
		else:
			return {'success': False, 'message': 'User is not active'}
	else:
		return {'success': False, 'message': 'User is not found'}
