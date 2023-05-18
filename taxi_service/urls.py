from django.urls import path, re_path
from taxi_service.views import index, about, why, agreement, blog
from django.views.i18n import JavaScriptCatalog

urlpatterns = [
    path('', index, name='index'),
    path('about/', about, name='about'),
    path('why/', why, name='why'),
    path('user-agreement/', agreement, name='user_agreement'),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog")
]
