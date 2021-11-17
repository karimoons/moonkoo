from django.urls import path

from . import views

app_name = 'employment_increase_tax_credit'

urlpatterns = [
    path('', views.index),
]