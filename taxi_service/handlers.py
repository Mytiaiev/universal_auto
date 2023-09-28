import json

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.contrib.auth import logout

from app.models import Manager, Partner
from taxi_service.forms import SubscriberForm, MainOrderForm, CommentForm
from taxi_service.utils import (update_order_sum_or_status, restart_order,
                                login_in, partner_logout, login_in_investor,
                                change_password_investor, send_reset_code,
                                active_vehicles_gps, order_confirm, effective_vehicle,
                                investor_cash_car, get_driver_info, partner_total_earnings,
                                manager_total_earnings, check_aggregators)

from auto.tasks import update_driver_data, get_uber_session, get_bolt_session, get_uklon_session, get_gps_session


class PostRequestHandler:
    def handler_order_form(self, request):
        order_form = MainOrderForm(request.POST)
        if order_form.is_valid():
            save_form = order_form.save(
                payment=request.POST.get('payment_method'),
                on_time=request.POST.get('order_time')
            )
            order_dict = model_to_dict(save_form)
            json_data = json.dumps(order_dict, cls=DjangoJSONEncoder)
            return JsonResponse({'data': json_data}, safe=False)
        else:
            return JsonResponse(order_form.errors, status=400)

    def handler_subscribe_form(self, request):
        sub_form = SubscriberForm(request.POST)
        if sub_form.is_valid():
            sub_form.save()
            return JsonResponse({}, status=200)
        else:
            return JsonResponse(sub_form.errors, status=400)

    def handler_comment_form(self, request):
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment_form.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse(
                {'success': False, 'errors': 'Щось пішло не так!'})

    def handler_update_order(self, request):
        id_order = request.POST.get('idOrder')
        action = request.POST.get('action')

        update_order_sum_or_status(id_order, action)

        return JsonResponse({}, status=200)

    def handler_restarting_order(self, request):
        id_order = request.POST.get('idOrder')
        car_delivery_price = request.POST.get('carDeliveryPrice', 0)
        action = request.POST.get('action')
        restart_order(id_order, car_delivery_price, action)

        return JsonResponse({}, status=200)

    def handler_success_login(self, request):
        action = request.POST.get('action')
        login = request.POST.get('login')
        password = request.POST.get('password')
        partner = Partner.objects.get(user=request.user.pk)

        def get_session_task(service_name):
            task = globals()[f'get_{service_name}_session'].delay(partner.pk, login=login, password=password)
            return JsonResponse({'task_id': task.id}, safe=False)

        if action in ['uber', 'bolt', 'uklon', 'gps']:
            response = HttpResponse(get_session_task(action), content_type='application/json')
        else:
            response = JsonResponse({'error': 'Invalid action'}, status=400)

        return response

    def handler_handler_logout(self, request):
        action = request.POST.get('action')
        partner = Partner.objects.get(user=request.user.pk)
        partner_logout(action, partner.pk)

        return JsonResponse({}, status=200)

    def handler_success_login_investor(self, request):
        login = request.POST.get('login')
        password = request.POST.get('password')

        success_login = login_in_investor(request, login, password)
        json_data = JsonResponse({'data': success_login}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handler_logout_investor(self, request):
        logout(request)
        return JsonResponse({'logged_out': True})

    def handler_change_password(self, request):
        if request.POST.get('action') == 'change_password':
            password = request.POST.get('password')
            new_password = request.POST.get('newPassword')
            user_email = User.objects.get(pk=request.user.pk).email

            change = change_password_investor(request, password, new_password, user_email)
            json_data = JsonResponse({'data': change}, safe=False)
            response = HttpResponse(json_data, content_type='application/json')
            return response

        if request.POST.get('action') == 'send_reset_code':
            email = request.POST.get('email')
            user = User.objects.filter(email=email).first()

            if user:
                user_login = user.username
                code = send_reset_code(email, user_login)
                json_data = JsonResponse({'code': code, 'success': True}, safe=False)
                response = HttpResponse(json_data, content_type='application/json')
                return response
            else:
                response = HttpResponse(json.dumps({'success': False}), content_type='application/json')
                return response

        if request.POST.get('action') == 'update_password':
            email = request.POST.get('email')
            new_password = request.POST.get('newPassword')
            user = User.objects.filter(email=email).first()
            if user:
                user.set_password(new_password)
                user.save()
                response = HttpResponse(json.dumps({'success': True}), content_type='application/json')
                return response
            else:
                response = HttpResponse(json.dumps({'success': False}), content_type='application/json')
                return response

    def handler_update_database(self, request):
        partner = Partner.objects.get(user=request.user.pk)
        upd = update_driver_data.delay(partner.pk)
        json_data = JsonResponse({'task_id': upd.id}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handler_unknown_action(self, request):
        return JsonResponse({}, status=400)


class GetRequestHandler:
    def handle_active_vehicles_locations(self, request):
        active_vehicle_locations = active_vehicles_gps()
        json_data = JsonResponse({'data': active_vehicle_locations}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_order_confirm(self, request):
        id_order = request.GET.get('id_order')
        driver = order_confirm(id_order)
        json_data = JsonResponse({'data': driver}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_get_investor_cash(self, request):
        period = request.GET.get('period')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        investor_id = request.user.pk

        get_cash = investor_cash_car(period, investor_id, start_date, end_date)
        json_data = JsonResponse({'data': get_cash}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_get_manager_cash(self, request):
        period = request.GET.get('period')
        user_id = request.user.pk
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        get_cash = manager_total_earnings(period, user_id, start_date, end_date)
        json_data = JsonResponse({'data': get_cash}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_get_partner_cash(self, request):
        period = request.GET.get('period')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        get_cash = partner_total_earnings(period, request.user.pk, start_date, end_date)
        json_data = JsonResponse({'data': get_cash}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_get_drivers_manager(self, request):
        action = request.GET.get('action')
        period = request.GET.get('period')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        driver_info = get_driver_info(request, period, request.user.pk, action, start_date, end_date)
        json_data = JsonResponse({'data': driver_info}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_get_drivers_partner(self, request):
        action = request.GET.get('action')
        period = request.GET.get('period')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        driver_info = get_driver_info(request, period, request.user.pk, action, start_date, end_date)
        json_data = JsonResponse({'data': driver_info}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_effective_vehicle(self, request):
        period = request.GET.get('period')
        action = request.GET.get('action')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        user_id = request.user.pk

        get_efficiency_vehicle = effective_vehicle(period, user_id, action, start_date, end_date)
        json_data = JsonResponse({'data': get_efficiency_vehicle}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_is_logged_in(self, request):
        if request.user.is_authenticated:
            user_name = request.user.first_name + " " + request.user.last_name

            response_data = {'is_logged_in': True, 'user_name': user_name}
        else:
            response_data = {'is_logged_in': False}
        return JsonResponse(response_data, safe=False)

    def handle_get_role(self, request):
        if request.user.is_authenticated:
            user_role = request.user.groups.first().name
            response_data = {'role': user_role}
        else:
            response_data = {'role': None}
        return JsonResponse(response_data, safe=False)

    def handle_check_aggregators(self, request):

        aggregators = check_aggregators(request.user.pk)
        json_data = JsonResponse({'data': aggregators}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_check_task(self, request):
        upd = update_driver_data.AsyncResult(request.GET.get('task_id'))
        if upd.ready():
            result = upd.get()
            json_data = JsonResponse({'data': result[1]}, safe=False)
            response = HttpResponse(json_data, content_type='application/json')
            return response
        else:
            json_data = JsonResponse({'data': 'in progress'}, safe=False)
            response = HttpResponse(json_data, content_type='application/json')
            return response

    def handle_unknown_action(self, request):
        return JsonResponse({}, status=400)
