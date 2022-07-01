from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required

import datetime
import pandas as pd
import numpy as np

from ..models import Family, Account, Ledger
from ..forms.forms import FinancialStatementsForm

@login_required
def dashboard(request):
    current_family = Family.objects.get(id=request.session['current_family_id'])

    return render(request, 'housekeeping_book/dashboard.html', {'current_family': current_family})

@login_required
def financial_statements(request):
    if request.method == 'POST':
        form = FinancialStatementsForm(request.POST)
        if form.is_valid():
            end_date1 = form.cleaned_data['date']
            if form.cleaned_data['unit'] == 'Y':
                start_date1 = datetime.date(end_date1.year, 1, 1)
                end_date0 = start_date1 - datetime.timedelta(days=1)
                start_date0 = datetime.date(end_date0.year, 1, 1)
            else:
                start_date1 = datetime.date(end_date1.year, end_date1.month, 1)
                end_date0 = start_date1 - datetime.timedelta(days=1)
                start_date0 = datetime.date(end_date0.year, end_date0.month, 1)
    else:
        form = FinancialStatementsForm()

        end_date1 = datetime.date.today()
        start_date1 = datetime.date(end_date1.year, end_date1.month, 1)
        end_date0 = start_date1 - datetime.timedelta(days=1)
        start_date0 = datetime.date(end_date0.year, end_date0.month, 1)

    family = Family.objects.get(id=request.session['current_family_id'])

    df_sofp1 = pd.DataFrame(Ledger.objects.filter(slit__family=family, slit__date__lte=end_date1, account__account__in=['A', 'L']).values())
    df_sofp0 = pd.DataFrame(Ledger.objects.filter(slit__family=family, slit__date__lt=start_date1, account__account__in=['A', 'L']).values())

    df_is1 = pd.DataFrame(Ledger.objects.filter(slit__family=family, slit__date__gte=start_date1, slit__date__lte=end_date1, account__account__in=['I', 'E']).values())
    df_is0 = pd.DataFrame(Ledger.objects.filter(slit__family=family, slit__date__gte=start_date0, slit__date__lte=end_date0, account__account__in=['I', 'E']).values())

    df_account = pd.DataFrame(Account.objects.filter(family=family).values())
    df_account.rename(columns = {'id': 'account_id'}, inplace=True)

    # 재무상태표 계산
    if df_sofp1.empty:
        df_sofp1_pt = pd.DataFrame(columns = ['account_id', 'amount1'])
    else:
        df_sofp1_pt = df_sofp1.pivot_table(values=['amount'], index=['account_id'], aggfunc='sum').reset_index().rename(columns={'amount': 'amount1'})

    if df_sofp0.empty:
        df_sofp0_pt = pd.DataFrame(columns = ['account_id', 'amount0'])
    else:
        df_sofp0_pt = df_sofp0.pivot_table(values=['amount'], index=['account_id'], aggfunc='sum').reset_index().rename(columns={'amount': 'amount0'})
    
    df_sofp = df_sofp1_pt.merge(df_sofp0_pt, on='account_id', how='outer').fillna(0).merge(df_account, on='account_id')[['code', 'account', 'title', 'amount1', 'amount0']]

    df_asset = df_sofp[df_sofp['account'] == 'A']
    df_liability = df_sofp[df_sofp['account'] == 'L']

    total_asset = {'current': df_asset['amount1'].sum(), 'previous': df_asset['amount0'].sum()}
    total_liability = {'current': df_liability['amount1'].sum(), 'previous': df_liability['amount0'].sum()}
    net_asset = {'current': total_asset['current'] - total_liability['current'], 'previous': total_asset['previous'] - total_liability['previous']}

    # 손익계산서 계산
    if df_is1.empty:
        df_is1_pt = pd.DataFrame(columns = ['account_id', 'amount1'])
    else:
        df_is1_pt = df_is1.pivot_table(values=['amount'], index=['account_id'], aggfunc='sum').reset_index().rename(columns={'amount': 'amount1'})
    
    if df_is0.empty:
        df_is0_pt = pd.DataFrame(columns = ['account_id', 'amount0'])
    else:
        df_is0_pt = df_is0.pivot_table(values=['amount'], index=['account_id'], aggfunc='sum').reset_index().rename(columns={'amount': 'amount0'})
    
    df_is = df_is1_pt.merge(df_is0_pt, on='account_id', how='outer').fillna(0).merge(df_account, on='account_id')[['code', 'account', 'title', 'amount1', 'amount0']]

    df_income = df_is[df_is['account'] == 'I']
    df_expense = df_is[df_is['account'] == 'E']

    total_income = {'current': df_income['amount1'].sum(), 'previous': df_income['amount0'].sum()}
    total_expense = {'current': df_expense['amount1'].sum(), 'previous': df_expense['amount0'].sum()}
    net_income = {'current': total_income['current'] - total_expense['current'], 'previous': total_income['previous'] - total_expense['previous']}

    context_dict = {
        'asset': df_asset,
        'liability': df_liability,
        'income': df_income,
        'expense': df_expense,
        'total_asset': total_asset,
        'total_liability': total_liability,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_asset': net_asset,
        'net_income': net_income,
        'form': form,
        'start_date1': start_date1,
        'end_date1': end_date1,
        'start_date0': start_date0,
        'end_date0': end_date0,
    }

    return render(request, 'housekeeping_book/financial_statements.html', context=context_dict)