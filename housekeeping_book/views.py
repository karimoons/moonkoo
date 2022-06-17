from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

import pandas as pd
import numpy as np

from .forms import ChoiceFamilyForm, CreateFamilyForm, CreateTransactionForm

from .models import Family, Slit, Account, Tag, Ledger

BASIC_ACCOUNT = {
    'code': [100, 110, 120, 200, 210, 300, 400, 410, 420, 430, 440, 450, 460, 510, 520, 530, 540, 550, 560, 570, 580, 590],
    'account': ['A', 'A', 'A', 'L', 'L', 'C', 'I', 'I', 'I', 'I', 'I', 'I', 'I', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E', 'E'],
    'title': ['저축', '주식', '부동산', '신용카드', '대출', '순자산', '근로소득', '콘텐츠소득', '사업소득', '부동산소득', '배당소득', '이자소득', '기타소득', '주거통신비', '보험의료비', '차량교통비', '식비', '생활용품비', '교육도서비', '모임경조사비', '이자비용', '기타비용'],
}

@login_required
def index(request):
    if request.method == 'POST':
        form = ChoiceFamilyForm(request.POST, user=request.user)
        if form.is_valid():
            request.session['current_family_id'] = request.POST['choice_family']

            return redirect(reverse('housekeeping_book:dashboard'))

    else:    
        form = ChoiceFamilyForm(user=request.user)

    return render(request, 'housekeeping_book/index.html', {'form': form})

@login_required
def create_family(request):
    if request.method == 'POST':
        form = CreateFamilyForm(request.POST)
        if form.is_valid():
            new_family = form.save()
            new_family.member.add(request.user)

            for num in range(len(BASIC_ACCOUNT['code'])):
                Account.objects.create(family=new_family, code=BASIC_ACCOUNT['code'][num], account=BASIC_ACCOUNT['account'][num], title=BASIC_ACCOUNT['title'][num])
            
            Tag.objects.create(family=new_family, name=new_family.name)

            return redirect(reverse('housekeeping_book:index'))
    else:
        form = CreateFamilyForm()

    return render(request, 'housekeeping_book/create_family.html', {'form': form})

@login_required
def invite_family(request):
    context_dict = {
        'fid': request.session['current_family_id'],
        'uid': request.user.username,
    }

    return render(request, 'housekeeping_book/invite_family.html', context=context_dict)

@login_required
def accept_invitation(request):
    if request.method == 'POST':
        family = Family.objects.get(id=request.POST['fid'])
        host = User.objects.get(username=request.POST['uid'])

        if host in family.member.all():
            family.member.add(request.user)
            return redirect(reverse('housekeeping_book:index'))
        else:
            return redirect(reverse('housekeeping_book:invitation_denied'))
            
    else:
        try:
            family = Family.objects.get(id=request.GET['fid'])
            host = User.objects.get(username=request.GET['uid'])
        except:
            return redirect(reverse('housekeeping_book:invitation_denied'))

    return render(request, 'housekeeping_book/accept_invitation.html', {'family': family, 'host': host})

@login_required
def invitation_denied(request):
    return render(request, 'housekeeping_book/invitation_denied.html')

@login_required
def dashboard(request):
    current_family = Family.objects.get(id=request.session['current_family_id'])

    return render(request, 'housekeeping_book/dashboard.html', {'current_family': current_family})

@login_required
def create_transaction(request):
    if request.method == 'POST':
        form = CreateTransactionForm(request.POST, current_family_id=request.session['current_family_id'])
        if form.is_valid():
            family = Family.objects.get(id=request.session['current_family_id'])
            main_account = Account.objects.get(family=family, title=form.cleaned_data['main_account'])
            main_tag = Tag.objects.get(family=family, name=form.cleaned_data['main_tag'])
            amount = form.cleaned_data['amount']
            sub_account = Account.objects.get(family=family, title=form.cleaned_data['sub_account'])
            sub_tag = Tag.objects.get(family=family, name=form.cleaned_data['sub_tag'])

            slit = Slit(family=family, date=form.cleaned_data['date'], memo=form.cleaned_data['memo'])
            slit.save()

            main_ledger = Ledger(slit=slit, account=main_account, tag=main_tag, amount=amount)

            if main_account.account == 'A':
                if sub_account.account in ['A', 'E']:
                    sub_amount = -amount
                else:
                    sub_amount = amount
            elif main_account.account == 'L':
                if sub_account.account in ['L', 'C', 'I']:
                    sub_amount= -amount
                else:
                    sub_amount = amount

            sub_ledger = Ledger(slit=slit, account=sub_account, tag=sub_tag, amount=sub_amount)

            main_ledger.save()
            sub_ledger.save()
    else:
        form = CreateTransactionForm(current_family_id=request.session['current_family_id'])

    return render(request, 'housekeeping_book/create_transaction.html', {'form': form})

@login_required
def financial_statements(request):
    family = Family.objects.get(id=request.session['current_family_id'])

    df_sofp = pd.DataFrame(Ledger.objects.filter(slit__family=family, account__account__in=['A', 'L']).values())
    df_is = pd.DataFrame(Ledger.objects.filter(slit__family=family, account__account__in=['I', 'E']).values())

    df_account = pd.DataFrame(Account.objects.filter(family=family).values())
    df_account.rename(columns = {'id': 'account_id'}, inplace=True)

    if df_sofp.empty:
        df_asset = pd.DataFrame()
        df_liability = pd.DataFrame()
    else:
        df_sofp = df_sofp.merge(df_account, on='account_id')

        df_asset = df_sofp[df_sofp['account'] == 'A'].pivot_table(values=['amount'], index=['code', 'title'], aggfunc=np.sum)
        df_liability = df_sofp[df_sofp['account'] == 'L'].pivot_table(values=['amount'], index=['code', 'title'], aggfunc=np.sum)

    if df_is.empty:
        df_income = pd.DataFrame()
        df_expense = pd.DataFrame()
    else:
        df_is = df_is.merge(df_account, on='account_id')

        df_income = df_is[df_is['account'] == 'I'].pivot_table(values=['amount'], index=['code', 'title'], aggfunc=np.sum)
        df_expense = df_is[df_is['account'] == 'E'].pivot_table(values=['amount'], index=['code', 'title'], aggfunc=np.sum)

    try:
        total_asset = df_asset.sum()['amount']
    except:
        total_asset = 0
    
    try:
        total_liability = df_liability.sum()['amount']
    except:
        total_liability = 0

    try:
        total_income = df_income.sum()['amount']
    except:
        total_income = 0
    
    try:
        total_expense = df_expense.sum()['amount']
    except:
        total_expense = 0

    context_dict = {
        'asset': df_asset,
        'liability': df_liability,
        'income': df_income,
        'expense': df_expense,
        'total_asset': total_asset,
        'total_liability': total_liability,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_asset': total_asset - total_liability,
        'net_income': total_income - total_expense,
    }

    return render(request, 'housekeeping_book/financial_statements.html', context=context_dict)