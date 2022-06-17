from django.urls import path

from . import views

app_name = 'housekeeping_book'

urlpatterns = [
    path('', views.index, name='index'),

    path('create-family/', views.create_family, name='create_family'),
    path('invite-family/', views.invite_family, name='invite_family'),
    path('accept-invitation/', views.accept_invitation, name='accept_invitation'),
    path('invitation-denied/', views.invitation_denied, name='invitation_denied'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('create-transaction/', views.create_transaction, name='create_transaction'),
    path('financial-statements/', views.financial_statements, name='financial_statements'),
]