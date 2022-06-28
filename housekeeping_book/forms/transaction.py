import datetime

from django import forms
from django.db.models import Q
from ..models import Account, Tag

class TransactionForm(forms.Form):
    date = forms.DateField(initial=datetime.date.today, widget=forms.DateInput(attrs={'type':'date'}))
    memo = forms.CharField(max_length=50)
    main_account = forms.ModelChoiceField(queryset=Account.objects.none())
    main_tag = forms.ModelChoiceField(queryset=Tag.objects.none())
    amount = forms.DecimalField(max_digits=13, decimal_places=0)
    sub_account = forms.ModelChoiceField(queryset=Account.objects.none())
    sub_tag = forms.ModelChoiceField(queryset=Tag.objects.none())

    def __init__(self, *args, **kwargs):
        current_family_id = kwargs.pop('current_family_id')
        date = kwargs.pop('date', '')
        memo = kwargs.pop('memo', '')
        main_account = kwargs.pop('main_account', '')
        main_tag = kwargs.pop('main_tag', '')
        amount = kwargs.pop('amount', '')
        sub_account = kwargs.pop('sub_account', '')
        sub_tag = kwargs.pop('sub_tag', '')

        super().__init__(*args, **kwargs)

        self.fields['main_account'].queryset = Account.objects.filter(Q(family__id=current_family_id)&(Q(account='A')|Q(account='L'))).order_by('code')
        self.fields['main_tag'].queryset = Tag.objects.filter(family__id=current_family_id).order_by('name')
        self.fields['sub_account'].queryset = Account.objects.filter(family__id=current_family_id).order_by('code')
        self.fields['sub_tag'].queryset = Tag.objects.filter(family__id=current_family_id).order_by('name')

        if date != '':
            self.fields['date'].initial = date
        if memo != '':
            self.fields['memo'].initial = memo

        if main_account != '':
            self.fields['main_account'].initial = main_account
        else:
            self.fields['main_account'].initial = self.fields['main_account'].queryset.first()

        if main_tag != '':
            self.fields['main_tag'].initial = main_tag
        else:
            self.fields['main_tag'].initial = self.fields['main_tag'].queryset.order_by('id').first()

        if amount != '':
            self.fields['amount'].initial = amount

        if sub_account != '':
            self.fields['sub_account'].initial = sub_account

        if sub_tag != '':
            self.fields['sub_tag'].initial = sub_tag
        else:
            self.fields['sub_tag'].initial = self.fields['sub_tag'].queryset.order_by('id').first()

class SearchForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type':'date'}))