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
            end_date = form.cleaned_data['date']
            if form.cleaned_data['unit'] == 'M':
                start_date = datetime.date(end_date.year, end_date.month, 1)
            else:
                start_date = datetime.date(end_date.year, 1, 1)
    else:
        form = FinancialStatementsForm()
        end_date = datetime.date.today()
        start_date = datetime.date(end_date.year, end_date.month, 1)

    family = Family.objects.get(id=request.session['current_family_id'])

    df_sofp = pd.DataFrame(Ledger.objects.filter(slit__family=family, slit__date__lte=end_date, account__account__in=['A', 'L']).values())
    df_is = pd.DataFrame(Ledger.objects.filter(slit__family=family, slit__date__gte=start_date, slit__date__lte=end_date, account__account__in=['I', 'E']).values())

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
        'form': form,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'housekeeping_book/financial_statements.html', context=context_dict)