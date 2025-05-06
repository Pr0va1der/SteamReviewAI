# accounts/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _  # <-- добавляем это

class SimpleUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': _('Логин')})  # перевод
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('Пароль')}),  # перевод
        required=True
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('Подтверждение пароля')}),  # перевод
        required=True
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': _('Логин')})  # перевод
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': _('Пароль')}),  # перевод
        required=True
    )

    class Meta:
        fields = ['username', 'password']
