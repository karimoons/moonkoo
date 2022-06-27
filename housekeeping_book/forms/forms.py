import datetime

from django import forms

class FinancialStatementsForm(forms.Form):
    unit = forms.ChoiceField(choices=(('M', '월간'), ('Y', '연간')), initial='M')
    date = forms.DateField(initial=datetime.date.today, widget=forms.DateInput(attrs={'type':'date'}))