from django import forms
from .models import Task, Comment
from datetime import date


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'status']  # assigned_to removed
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['due_date'].widget.attrs['min'] = date.today().isoformat()

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date and due_date < date.today():
            # Allow editing an existing task whose due_date is already past
            original = getattr(self.instance, 'due_date', None)
            if due_date != original:
                raise forms.ValidationError("Due date cannot be in the past.")
        return due_date

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Leave a comment...'}),
        }
        labels = {
            'text': ''
        }