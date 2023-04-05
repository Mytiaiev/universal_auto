from django.urls import path
from taxi_service.views import index, about, why, agreement, blog

urlpatterns = [
    path('', index, name='index'),
    path('about/', about, name='about'),
    path('why/', why, name='why'),
    path('user-agreement/', agreement, name='user_agreement')
]
