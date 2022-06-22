from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from ..forms import AccountForm

from ..models import Family, Account

@login_required
def account_list(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)

        if form.is_valid():
            new_account = form.save(commit=False)
            new_account.family = Family.objects.get(id=request.session['current_family_id'])

            try:
                new_account.save()
            except:
                messages.error(request, '계정코드 또는 계정과목은 중복될 수 없습니다.')
    else:
        form = AccountForm()
    
    account_list = Account.objects.filter(family=request.session['current_family_id']).order_by('code')

    return render(request, 'housekeeping_book/account/account_list.html', {'account_list': account_list, 'form': form})

@login_required
def update_account(request, pk):
    if request.method == 'POST':
        form = AccountForm(request.POST)

        if form.is_valid():
            account = form.save(commit=False)
            account.id = pk
            account.family = Family.objects.get(id=request.session['current_family_id'])

            try:
                account.save()
                return redirect(reverse('housekeeping_book:account_list'))
            except:
                messages.error(request, '계정코드 또는 계정과목은 중복될 수 없습니다.')
    else:
        form = AccountForm(instance=Account.objects.get(id=pk))

    return render(request, 'housekeeping_book/account/update_account.html', {'form': form, 'pk': pk})

@login_required
def delete_account(request, pk):
    account = Account.objects.get(id=pk)

    if request.method == 'POST':
        if request.user in account.family.member.all():
            account.delete()
            return redirect(reverse('housekeeping_book:account_list'))
        else:
            messages.error(request, '계정과목을 삭제할 권한이 없습니다.')

    return render(request, 'housekeeping_book/account/delete_account.html', {'account': account})