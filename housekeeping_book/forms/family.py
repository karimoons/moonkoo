from django import forms
from ..models import Family

class ChoiceFamilyForm(forms.Form):
    choice_family = forms.ModelChoiceField(queryset=Family.objects.none())

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super().__init__(*args, **kwargs)
        self.fields['choice_family'].queryset = Family.objects.filter(member=user)
        self.fields['choice_family'].initial = self.fields['choice_family'].queryset.first()

class CreateFamilyForm(forms.ModelForm):
    class Meta:
        model = Family
        fields = ['name', ]