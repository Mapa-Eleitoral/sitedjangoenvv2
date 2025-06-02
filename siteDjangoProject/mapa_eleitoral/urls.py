# mapa_eleitoral/urls.py (URLs do app)
from django.urls import path
from . import views

app_name = 'mapa_eleitoral'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('get-candidatos/', views.get_candidatos_ajax, name='get_candidatos'),
]

