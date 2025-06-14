from django import forms
from .models import SignupRequest, CustomUser

class SignupRequestForm(forms.ModelForm):
    class Meta:
        model = SignupRequest
        fields = ['name', 'employee_id']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'department', 'phone_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
        }