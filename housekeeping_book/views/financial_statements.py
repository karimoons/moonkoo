from django.shortcuts import render
from django.contrib.auth.decorators import login_required

import datetime
import pandas as pd

from ..models import Family, Account, Ledger
from ..forms.forms import FinancialStatementsForm

@login_required
def financial_statements(request):
    if request.method == 'POST':
        form = FinancialStatementsForm(request.POST)
        if form.is_valid():
            unit = form.cleaned_data['unit']
            end_date1 = form.cleaned_data['date']

            request.session['fs_unit'] = form.cleaned_data['unit']
            request.session['fs_end_date'] = str(end_date1)

    else:
        if request.session.get('fs_unit') and request.session.get('fs_end_date'):
            form = FinancialStatementsForm(initial={'unit': request.session.get('fs_unit'), 'date': request.session.get('fs_end_date')})

            unit = request.session.get('fs_unit')
            end_date1 = datetime.datetime.strptime(request.session.get('fs_end_date'), '%Y-%m-%d').date()

        else:
            form = FinancialStatementsForm()

            end_date1 = datetime.date.today()

    if unit == 'Y':
        start_date1 = datetime.date(end_date1.year, 1, 1)
        end_date0 = start_date1 - datetime.timedelta(days=1)
        start_date0 = datetime.date(end_date0.year, 1, 1)
    else:
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
    
    df_sofp = df_sofp1_pt.merge(df_sofp0_pt, on='account_id', how='outer').fillna(0).merge(df_account, on='account_id')[['code', 'account', 'classification', 'title', 'amount1', 'amount0']]

    df_asset = df_sofp[df_sofp['account'] == 'A']
    df_current_asset = df_asset[df_asset['classification'] == 'C']
    df_noncurrent_asset = df_asset[df_asset['classification'] == 'NC']

    df_liability = df_sofp[df_sofp['account'] == 'L']
    df_current_liability = df_liability[df_liability['classification'] == 'C']
    df_noncurrent_liability = df_liability[df_liability['classification'] == 'NC']

    total = {}

    total['asset'] = {'current': df_asset['amount1'].sum(), 'previous': df_asset['amount0'].sum()}
    total['current_asset'] = {'current': df_current_asset['amount1'].sum(), 'previous': df_current_asset['amount0'].sum()}
    total['noncurrent_asset'] = {'current': df_noncurrent_asset['amount1'].sum(), 'previous': df_noncurrent_asset['amount0'].sum()}

    total['liability'] = {'current': df_liability['amount1'].sum(), 'previous': df_liability['amount0'].sum()}
    total['current_liability'] = {'current': df_current_liability['amount1'].sum(), 'previous': df_current_liability['amount0'].sum()}
    total['noncurrent_liability'] = {'current': df_noncurrent_liability['amount1'].sum(), 'previous': df_noncurrent_liability['amount0'].sum()}

    total['net_asset'] = {'current': total['asset']['current'] - total['liability']['current'], 'previous': total['asset']['previous'] - total['liability']['previous']}

    # 손익계산서 계산
    if df_is1.empty:
        df_is1_pt = pd.DataFrame(columns = ['account_id', 'amount1'])
    else:
        df_is1_pt = df_is1.pivot_table(values=['amount'], index=['account_id'], aggfunc='sum').reset_index().rename(columns={'amount': 'amount1'})
    
    if df_is0.empty:
        df_is0_pt = pd.DataFrame(columns = ['account_id', 'amount0'])
    else:
        df_is0_pt = df_is0.pivot_table(values=['amount'], index=['account_id'], aggfunc='sum').reset_index().rename(columns={'amount': 'amount0'})
    
    df_is = df_is1_pt.merge(df_is0_pt, on='account_id', how='outer').fillna(0).merge(df_account, on='account_id')[['code', 'account', 'classification', 'title', 'amount1', 'amount0']]

    df_income = df_is[df_is['account'] == 'I']
    df_fixed_income = df_income[df_income['classification'] == 'F']
    df_variable_income = df_income[df_income['classification'] == 'V']

    df_expense = df_is[df_is['account'] == 'E']
    df_fixed_expense = df_expense[df_expense['classification'] == 'F']
    df_variable_expense = df_expense[df_expense['classification'] == 'V']

    total['fixed_income'] = {'current': df_fixed_income['amount1'].sum(), 'previous': df_fixed_income['amount0'].sum()}
    total['fixed_expense'] = {'current': df_fixed_expense['amount1'].sum(), 'previous': df_fixed_expense['amount0'].sum()}
    total['fixed_profit'] = {'current': total['fixed_income']['current'] - total['fixed_expense']['current'], 'previous': total['fixed_income']['previous'] - total['fixed_expense']['previous']}

    total['variable_income'] = {'current': df_variable_income['amount1'].sum(), 'previous': df_variable_income['amount0'].sum()}
    total['variable_expense'] = {'current': df_variable_expense['amount1'].sum(), 'previous': df_variable_expense['amount0'].sum()}
    total['net_income'] = {'current': total['fixed_profit']['current'] + total['variable_income']['current'] - total['variable_expense']['current'], 'previous': total['fixed_profit']['previous'] + total['variable_income']['previous'] + total['variable_expense']['previous']}
    
    context_dict = {
        'current_asset': df_current_asset,
        'noncurrent_asset': df_noncurrent_asset,
        'current_liability': df_current_liability,
        'noncurrent_liability': df_noncurrent_liability,
        'fixed_income': df_fixed_income,
        'variable_income': df_variable_income,
        'fixed_expense': df_fixed_expense,
        'variable_expense': df_variable_expense,
        'total': total,
        'form': form,
        'start_date1': start_date1,
        'end_date1': end_date1,
        'start_date0': start_date0,
        'end_date0': end_date0,
    }

    return render(request, 'housekeeping_book/financial_statements/financial_statements.html', context=context_dict)