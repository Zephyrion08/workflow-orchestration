from django import forms
from .models import SignupRequest, CustomUser

class SignupRequestForm(forms.ModelForm):
    class Meta:
        model = SignupRequest
        fields = ['name', 'employee_id']

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters.")
        return name

    def clean_employee_id(self):
        employee_id = self.cleaned_data.get('employee_id', '').strip()
        if not employee_id.isalnum():
            raise forms.ValidationError("Employee ID must be alphanumeric.")
            
        if SignupRequest.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError("This Employee ID has already been requested.")
        if CustomUser.objects.filter(employee_id=employee_id).exists():
            raise forms.ValidationError("This Employee ID is already registered.")
        return employee_id

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