from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('sapata', views.sapata_view, name='sapata'),
    path('calculate_sapata', views.calculate_sapata_view, name='calculate_sapata'),
]

