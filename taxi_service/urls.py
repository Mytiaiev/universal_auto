from django.urls import path
from taxi_service.views import index, about, why, blog


urlpatterns = [
    path('', index, name='index'),
    path('about/', about, name='about'),
    path('blog/', blog, name='blog'),
    path('why/', why, name='why'),
]
