import datetime
from urllib.parse import urlencode

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum

import pandas as pd

from ..forms.transaction import TransactionForm, SearchForm

from ..models import Family, Slit, Account, Tag, Ledger

@login_required
def transaction_list(request, code):
    family = Family.objects.get(id=request.session['current_family_id'])
    main_account = Account.objects.filter(family=family).get(code=code)
    ledgers = Ledger.objects.filter(slit__family=family).filter(account=main_account).order_by('slit__date')
    balance_ledgers = ledgers

    form = SearchForm(request.GET)
    if form.is_valid():
        cd = form.cleaned_data

        if cd['start_date']:
            balance_ledgers = balance_ledgers.filter(slit__date__lt=str(cd['start_date']))
            if main_account.account in ['I', 'E']:
                balance_ledgers = balance_ledgers.filter(slit__date__gte=str(datetime.date(cd['start_date'].year, 1, 1)))

            ledgers = ledgers.filter(slit__date__gte=str(cd['start_date']))
        if cd['end_date']:
            ledgers = ledgers.filter(slit__date__lte=str(cd['end_date']))
        if cd['memo']:
            ledgers = ledgers.filter(slit__memo__contains=cd['memo'])
            balance_ledgers = balance_ledgers.filter(slit__memo__contains=cd['memo'])
        if cd['tag']:
            ledgers = ledgers.filter(tag__name__contains=cd['tag'])
            balance_ledgers = balance_ledgers.filter(tag__name__contains=cd['tag'])
        
        init_balance = balance_ledgers.aggregate(Sum('amount'))['amount__sum'] or 0
        balance = init_balance
        balance_list = []
        
        for ledger in ledgers:
            balance = balance + ledger.amount
            balance_list.append(balance)
        
        zipped_ledgers = zip(ledgers, balance_list)

    return render(request, 'housekeeping_book/transaction/transaction_list.html', {'main_account': main_account, 'init_balance': init_balance, 'zipped_ledgers': zipped_ledgers, 'form': form})

@login_required
def transaction_summary(request, code):
    family = Family.objects.get(id=request.session['current_family_id'])
    main_account = Account.objects.filter(family=family).get(code=code)
    ledgers = Ledger.objects.filter(slit__family=family).filter(account=main_account).order_by('slit__date')
    balance_ledgers = ledgers
    tags = Tag.objects.filter(family=family)

    url_parameter = {'code': code}

    form = SearchForm(request.GET)
    if form.is_valid():
        cd = form.cleaned_data

        if cd['start_date']:
            balance_ledgers = balance_ledgers.filter(slit__date__lt=str(cd['start_date']))
            ledgers = ledgers.filter(slit__date__gte=str(cd['start_date']))
            
            url_parameter['start_date'] = str(cd['start_date'])

        if cd['end_date']:
            ledgers = ledgers.filter(slit__date__lte=str(cd['end_date']))

            url_parameter['end_date'] = str(cd['end_date'])
    
    df_balance_ledgers = pd.DataFrame(balance_ledgers.values())
    try:
        df_balance_ledgers_pt = df_balance_ledgers.pivot_table(values=['amount'], index=['tag_id'], aggfunc='sum')
        df_balance_ledgers_pt.rename(columns={'amount': 'init_balance'}, inplace=True)
    except:
        df_balance_ledgers_pt = pd.DataFrame(columns=['tag_id', 'init_balance']).set_index('tag_id')

    df_ledgers = pd.DataFrame(ledgers.values())
    try:
        df_ledgers_pt = df_ledgers.pivot_table(values=['amount'], index=['tag_id'], aggfunc='sum')
    except:
        df_ledgers_pt = pd.DataFrame(columns=['tag_id', 'amount']).set_index('tag_id')

    df_summary = df_balance_ledgers_pt.join(df_ledgers_pt, how='outer').fillna(0)
    df_summary['balance'] = df_summary['init_balance'] + df_summary['amount']

    df_tags = pd.DataFrame(tags.values())
    df_tags.rename(columns = {'id': 'tag_id', 'name': 'tag_name'}, inplace=True)
    df_tags = df_tags.set_index('tag_id')

    df_summary = df_summary.join(df_tags)

    total = {'init_balance': df_summary['init_balance'].sum, 'amount': df_summary['amount'].sum, 'balance': df_summary['balance'].sum}

    return render(request, 'housekeeping_book/transaction/transaction_summary.html', {'summary': df_summary, 'total': total, 'form': form, 'url_parameter': url_parameter})

@login_required
def create_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST, current_family_id=request.session['current_family_id'])
        if form.is_valid():
            family = Family.objects.get(id=request.session['current_family_id'])
            main_account = Account.objects.get(family=family, title=form.cleaned_data['main_account'])
            main_tag = Tag.objects.get(family=family, name=form.cleaned_data['main_tag'])
            amount = form.cleaned_data['amount']
            sub_account = Account.objects.get(family=family, title=form.cleaned_data['sub_account'])
            sub_tag = Tag.objects.get(family=family, name=form.cleaned_data['sub_tag'])

            slit = Slit(family=family, date=form.cleaned_data['date'], memo=form.cleaned_data['memo'], modified_user=request.user)
            slit.save()

            main_ledger = Ledger(slit=slit, account=main_account, tag=main_tag, amount=amount, opposite_account=sub_account, opposite_tag=sub_tag)

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

            sub_ledger = Ledger(slit=slit, account=sub_account, tag=sub_tag, amount=sub_amount, opposite_account=main_account, opposite_tag=main_tag)

            main_ledger.save()
            sub_ledger.save()

            end_date = slit.date
            start_date = end_date - datetime.timedelta(days=7)
            tag = main_ledger.tag.name

            base_url = reverse('housekeeping_book:transaction_list', args=(main_ledger.account.code, ))
            query_string = urlencode({'start_date': start_date, 'end_date': end_date, 'tag': tag})
            url = '{}?{}'.format(base_url, query_string)

            return redirect(url)

    form = TransactionForm(current_family_id=request.session['current_family_id'])

    return render(request, 'housekeeping_book/transaction/update_transaction.html', {'form': form})

@login_required
def update_transaction(request, pk):
    slit = Slit.objects.get(id=pk)
    ledgers = slit.ledger_set.all()

    main_ledger = ledgers[0]
    sub_ledger = ledgers[1]

    if request.GET.get('code'):
        request.session['transaction_list_code'] = request.GET.get('code')
    if request.GET.get('start_date'):
        request.session['transaction_list_start_date'] = request.GET.get('start_date')
    if request.GET.get('end_date'):
        request.session['transaction_list_end_date'] = request.GET.get('end_date')
    if request.GET.get('memo'):
        request.session['transaction_list_memo'] = request.GET.get('memo')
    if request.GET.get('tag'):
        request.session['transaction_list_tag'] = request.GET.get('tag')

    if request.method == 'POST':
        form = TransactionForm(request.POST, current_family_id=request.session['current_family_id'])

        if form.is_valid():
            slit.date = form.cleaned_data['date']
            slit.memo = form.cleaned_data['memo']
            slit.modified_user = request.user

            main_ledger.account = form.cleaned_data['main_account']
            main_ledger.tag = form.cleaned_data['main_tag']
            main_ledger.amount = form.cleaned_data['amount']
            main_ledger.opposite_account = form.cleaned_data['sub_account']
            main_ledger.opposite_tag = form.cleaned_data['sub_tag']

            sub_ledger.account = form.cleaned_data['sub_account']
            sub_ledger.tag = form.cleaned_data['sub_tag']

            if main_ledger.account.account == 'A':
                if sub_ledger.account.account in ['A', 'E']:
                    sub_ledger.amount = -main_ledger.amount
                else:
                    sub_ledger.amount = main_ledger.amount
            elif main_ledger.account.account == 'L':
                if sub_ledger.account.account in ['L', 'C', 'I']:
                    sub_ledger.amount = -main_ledger.amount
                else:
                    sub_ledger.amount = main_ledger.amount
            
            sub_ledger.opposite_account = form.cleaned_data['main_account']
            sub_ledger.opposite_tag = form.cleaned_data['main_tag']
        
            slit.save()
            main_ledger.save()
            sub_ledger.save()

            base_url = reverse('housekeeping_book:transaction_list', args=(request.session.pop('transaction_list_code'), ))
            query_string = urlencode({'start_date': request.session.pop('transaction_list_start_date', ''), 'end_date': request.session.pop('transaction_list_end_date', ''), 'memo': request.session.pop('transaction_list_memo', ''), 'tag': request.session.pop('transaction_list_tag', '')})
            url = '{}?{}'.format(base_url, query_string)

            return redirect(url)

    else:
        form = TransactionForm(current_family_id=request.session['current_family_id'], date=slit.date, memo=slit.memo, main_account=main_ledger.account, main_tag=main_ledger.tag, amount=main_ledger.amount, sub_account=main_ledger.opposite_account, sub_tag=main_ledger.opposite_tag)

    return render(request, 'housekeeping_book/transaction/update_transaction.html', {'form': form, 'pk': pk, 'slit': slit})

@login_required
def delete_transaction(request, pk):
    slit = Slit.objects.get(id=pk)

    if request.method == 'POST':
        slit.delete()

        return redirect(reverse('housekeeping_book:financial_statements'))

    return render(request, 'housekeeping_book/transaction/delete_transaction.html', {'slit': slit})