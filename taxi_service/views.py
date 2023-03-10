from django.http import JsonResponse
from django.shortcuts import render
from taxi_service.forms import SubscriberForm, MainOrderForm


def index(request):
    sub_form = SubscriberForm()
    order_form = MainOrderForm()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.POST.get('action') == 'order':
            order_form = MainOrderForm(request.POST)
            if order_form.is_valid():
                order_form.save()
            else:
                return JsonResponse(order_form.errors, status=400)

        elif request.POST.get('action') == 'subscribe':
            sub_form = SubscriberForm(request.POST)
            if sub_form.is_valid():
                sub_form.save()
            else:
                return JsonResponse(sub_form.errors, status=400)

    context = {
        "subscribe_form": sub_form,
        "order_form": order_form,
    }

    return render(request, 'index.html', context)


def about(request):
    return render(request, 'about.html')


def blog(request):
    return render(request, 'blog.html')


def why(request):
    return render(request, 'why.html')





