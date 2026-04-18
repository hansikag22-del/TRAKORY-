from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ContentItem, ALL_STATUS_CHOICES, CATEGORY_CHOICES

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-input'

class ContentItemForm(forms.ModelForm):
    class Meta:
        model = ContentItem
        fields = ['title', 'category', 'status', 'rating', 'progress', 'total', 'genre', 'notes']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter title...'}),
            'category': forms.Select(attrs={'class': 'form-input', 'id': 'id_category'}),
            'status': forms.Select(attrs={'class': 'form-input', 'id': 'id_status'}),
            'rating': forms.Select(attrs={'class': 'form-input'}),
            'progress': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'total': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'genre': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Action, Romance...'}),
            'notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Your notes...'}),
        }
