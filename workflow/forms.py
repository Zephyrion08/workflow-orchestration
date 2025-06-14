from django import forms
from django.contrib.auth.models import Group
from .models import Task
from accounts.models import CustomUser  # adjust import if needed

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
