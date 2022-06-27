import datetime

from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from ..forms.transaction import TransactionForm, SearchForm

from ..models import Family, Slit, Account, Tag, Ledger

@login_required
def transaction_list(request, code):
    family = Family.objects.get(id=request.session['current_family_id'])
    main_account = Account.objects.filter(family=family).get(code=code)
    ledgers = Ledger.objects.filter(slit__family=family).filter(account=main_account).order_by('slit__date')

    if 'end_date' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            if form.cleaned_data['start_date']:
                start_date = form.cleaned_data['start_date']
            else:
                start_date = form.cleaned_data['end_date'] - datetime.timedelta(days=7)

            if form.cleaned_data['end_date']:
                end_date = form.cleaned_data['end_date']
            else:
                end_date = datetime.date.today()

            ledgers = ledgers.filter(slit__date__gte=start_date, slit__date__lte=end_date)
    else:
        form = SearchForm()

    return render(request, 'housekeeping_book/transaction/transaction_list.html', {'main_account': main_account, 'ledgers': ledgers, 'form': form})

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

            slit = Slit(family=family, date=form.cleaned_data['date'], memo=form.cleaned_data['memo'])
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

    form = TransactionForm(current_family_id=request.session['current_family_id'])

    return render(request, 'housekeeping_book/transaction/update_transaction.html', {'form': form})

@login_required
def update_transaction(request, pk):
    slit = Slit.objects.get(id=pk)
    ledgers = slit.ledger_set.all()

    main_ledger = ledgers[0]
    sub_ledger = ledgers[1]

    if request.method == 'POST':
        form = TransactionForm(request.POST, current_family_id=request.session['current_family_id'])

        if form.is_valid():
            slit.date = form.cleaned_data['date']
            slit.memo = form.cleaned_data['memo']

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

            print(request.POST.get('next'))
            print(request.POST.get('next', '/'))

            return redirect(request.POST.get('next'))

    else:
        form = TransactionForm(current_family_id=request.session['current_family_id'], date=slit.date, memo=slit.memo, main_account=main_ledger.account, main_tag=main_ledger.tag, amount=main_ledger.amount, sub_account=main_ledger.opposite_account, sub_tag=main_ledger.opposite_tag)

    return render(request, 'housekeeping_book/transaction/update_transaction.html', {'form': form, 'pk': pk})

@login_required
def delete_transaction(request, pk):
    slit = Slit.objects.get(id=pk)

    if request.method == 'POST':
        slit.delete()

        return redirect(reverse('housekeeping_book:financial_statements'))

    return render(request, 'housekeeping_book/transaction/delete_transaction.html', {'slit': slit})