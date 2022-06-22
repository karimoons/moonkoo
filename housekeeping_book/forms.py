import datetime

from django import forms
from django.db.models import Q
from .models import Family, Account, Tag

class ChoiceFamilyForm(forms.Form):
    choice_family = forms.ModelChoiceField(queryset=Family.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['choice_family'].queryset = Family.objects.filter(member=user)

class CreateFamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ['name', ]

class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['code', 'account', 'title', ]

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', ]

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

        super().__init__(*args, **kwargs)

        self.fields['main_account'].queryset = Account.objects.filter(Q(family__id=current_family_id)&(Q(account='A')|Q(account='L'))).order_by('code')
        self.fields['main_tag'].queryset = Tag.objects.filter(family__id=current_family_id).order_by('name')
        self.fields['sub_account'].queryset = Account.objects.filter(family__id=current_family_id).order_by('code')
        self.fields['sub_tag'].queryset = Tag.objects.filter(family__id=current_family_id).order_by('name')

        self.fields['main_account'].initial = self.fields['main_account'].queryset.first()
        self.fields['main_tag'].initial = self.fields['main_tag'].queryset.first()
        self.fields['sub_tag'].initial = self.fields['sub_tag'].queryset.first()