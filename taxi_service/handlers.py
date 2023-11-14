import json

from celery.result import AsyncResult
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.forms.models import model_to_dict
from django.contrib.auth import logout

from app.models import Partner, Manager, SubscribeUsers
from taxi_service.forms import SubscriberForm, MainOrderForm, CommentForm
from taxi_service.utils import (update_order_sum_or_status, restart_order,
                                partner_logout, login_in_investor,
                                change_password_investor, send_reset_code,
                                active_vehicles_gps, order_confirm,
                                check_aggregators)

from auto.tasks import update_driver_data, get_session


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
        aggregator = request.POST.get('aggregator')
        login = request.POST.get('login')
        password = request.POST.get('password')
        partner = Partner.objects.get(user=request.user.pk)
        task = get_session.delay(partner.pk, aggregator, login=login, password=password)
        json_data = JsonResponse({'task_id': task.id}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')

        return response

    def handler_handler_logout(self, request):
        aggregator = request.POST.get('aggregator')
        partner = Partner.objects.get(user=request.user.pk)
        partner_logout(aggregator, partner.pk)

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
        if request.user.groups.filter(name="Partner").exists():
            partner = Partner.objects.get(user=request.user.pk).pk
        else:
            partner = Manager.objects.get(user=request.user.pk).partner.pk
        upd = update_driver_data.delay(partner)
        json_data = JsonResponse({'task_id': upd.id}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handler_free_access(self, request):
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        response_data = {'success': False, 'error': 'Ви вже підписались'}
        phone = phone.replace(' ', '').replace('-', '')
        user, created = SubscribeUsers.objects.get_or_create(phone_number=phone,
                                                             defaults={"name": name})
        if created:
            response_data = {'success': True}

        json_data = JsonResponse(response_data, safe=False)
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

    def handle_get_role(self, request):
        if request.user.is_authenticated:
            user_role = request.user.groups.first().name
            response_data = {'role': user_role}
        else:
            response_data = {'role': None}
        return JsonResponse(response_data, safe=False)

    def handle_check_aggregators(self, request):
        aggregators, fleets = check_aggregators(request.user.pk)
        json_data = JsonResponse({'data': aggregators, 'fleets': fleets}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_check_task(self, request):
        upd = AsyncResult(request.GET.get('task_id'))
        answer = upd.get()[1] if upd.ready() else 'in progress'
        json_data = JsonResponse({'data': answer}, safe=False)
        response = HttpResponse(json_data, content_type='application/json')
        return response

    def handle_unknown_action(self, request):
        return JsonResponse({}, status=400)
