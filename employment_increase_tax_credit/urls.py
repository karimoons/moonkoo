from django.urls import path

from . import views

app_name = 'employment_increase_tax_credit'

urlpatterns = [
    path('', views.index, name='index'),
    path('social-insurance/', views.social_insurance, name='social_insurance'),
]