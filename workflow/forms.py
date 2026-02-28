from django import forms
from django.contrib.auth.models import Group
from .models import Task
from accounts.models import CustomUser
from datetime import date


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_to', 'due_date', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_to': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        admin_group = Group.objects.filter(name='Admin').first()
        qs = CustomUser.objects.filter(is_active=True, is_superuser=False)
        if admin_group:
            qs = qs.exclude(groups=admin_group)
        self.fields['assigned_to'].queryset = qs.order_by('username')

        # Prevent past dates at browser level
        self.fields['due_date'].widget.attrs['min'] = date.today().isoformat()

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < date.today():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date