from django import forms
from apps.clients.models import Client, Contact


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'name', 'client_type', 'inn', 'phone', 'email',
            'address', 'category', 'manager', 'notes',
        ]
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control'}),
            'client_type': forms.Select(attrs={'class': 'form-select'}),
            'inn':         forms.TextInput(attrs={'class': 'form-control'}),
            'phone':       forms.TextInput(attrs={'class': 'form-control'}),
            'email':       forms.EmailInput(attrs={'class': 'form-control'}),
            'address':     forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'category':    forms.Select(attrs={'class': 'form-select'}),
            'manager':     forms.Select(attrs={'class': 'form-select select2'}),
            'notes':       forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['full_name', 'position', 'phone', 'email', 'is_primary', 'notes']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'position':  forms.TextInput(attrs={'class': 'form-control'}),
            'phone':     forms.TextInput(attrs={'class': 'form-control'}),
            'email':     forms.EmailInput(attrs={'class': 'form-control'}),
            'notes':     forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
