from django.urls import path

from .views import family
from .views import account
from .views import tag

from .views import views

app_name = 'housekeeping_book'

urlpatterns = [
    path('', family.select_family, name='select_family'),

    path('family/create/', family.create_family, name='create_family'),
    path('family/invite/', family.invite_family, name='invite_family'),
    path('accept-invitation/', family.accept_invitation, name='accept_invitation'),
    path('invitation-denied/', family.invitation_denied, name='invitation_denied'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('account/list/', account.account_list, name='account_list'),
    path('account/update/<int:pk>/', account.update_account, name='update_account'),
    path('account/delete/<int:pk>/', account.delete_account, name='delete_account'),

    path('tag/list/', tag.TagListView.as_view(), name='tag_list'),
    path('tag/create/', tag.create_tag, name='create_tag'),
    path('tag/update/<int:pk>/', tag.update_tag, name='update_tag'),
    path('tag/delete/<int:pk>/', tag.delete_tag, name='delete_tag'),

    path('create-transaction/', views.create_transaction, name='create_transaction'),
    path('financial-statements/', views.financial_statements, name='financial_statements'),
]