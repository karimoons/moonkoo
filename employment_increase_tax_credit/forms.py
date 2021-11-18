from django import forms

class DateForm(forms.Form):
    date = forms.DateField()

class UploadFileForm(forms.Form):
    file = forms.FileField()