from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from ..forms.account import AccountForm

from ..models import Family, Account

@login_required
def account_list(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)

        if form.is_valid():
            new_account = form.save(commit=False)
            new_account.family = Family.objects.get(id=request.session['current_family_id'])
            new_account.modified_user = request.user

            if new_account.account in ['A', 'L'] and new_account.classification not in ['C', 'NC']:
                messages.error(request, '자산 또는 부채 계정의 분류는 유동 또는 비유동만 선택할 수 있습니다.')
            elif new_account.account == 'C' and new_account.classification not in ['R', 'UR']:
                messages.error(request, '자본 계정의 분류는 실현 또는 미실현만 선택할 수 있습니다.')
            elif new_account.account in ['I', 'E'] and new_account.classification not in ['O', 'NO']:
                messages.error(request, '수익 또는 비용 계정의 분류는 경상 또는 비경상만 선택할 수 있습니다.')
            else:
                try:
                    new_account.save()
                    form = AccountForm()
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
            account.modified_user = request.user

            if account.account in ['A', 'L'] and account.classification not in ['C', 'NC']:
                messages.error(request, '자산 또는 부채 계정의 분류는 유동 또는 비유동만 선택할 수 있습니다.')
            elif account.account == 'C' and account.classification not in ['R', 'UR']:
                messages.error(request, '자본 계정의 분류는 실현 또는 미실현만 선택할 수 있습니다.')
            elif account.account in ['I', 'E'] and account.classification not in ['O', 'NO']:
                messages.error(request, '수익 또는 비용 계정의 분류는 경상 또는 비경상만 선택할 수 있습니다.')
            else:
                try:
                    account.save()
                    return redirect(reverse('housekeeping_book:account_list'))
                except:
                    messages.error(request, '계정코드 또는 계정과목은 중복될 수 없습니다.')
    else:
        account = Account.objects.get(id=pk)
        form = AccountForm(instance=account)

    return render(request, 'housekeeping_book/account/update_account.html', {'form': form, 'pk': pk, 'account': account})

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