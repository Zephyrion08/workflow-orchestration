from django import forms
from .models import SignupRequest

class SignupRequestForm(forms.ModelForm):
    class Meta:
        model = SignupRequest
        fields = ['name', 'employee_id']
