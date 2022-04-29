from django.urls import path

from . import views

app_name = 'housekeeping_book'

urlpatterns = [
    path('', views.index, name='index'),
    path('create-family/', views.create_family, name='create_family'),
    path('dashboard/', views.dashboard, name='dashboard'),
]