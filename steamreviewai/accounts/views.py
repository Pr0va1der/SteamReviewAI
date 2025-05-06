from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .forms import SimpleUserCreationForm, CustomAuthenticationForm

def register(request):
    if request.method == 'POST':
        form = SimpleUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Сохраняем нового пользователя
            login(request, user)  # Автоматически входим
            return redirect('/')  # Перенаправляем на главную страницу
    else:
        form = SimpleUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == "POST":
        form = CustomAuthenticationForm(request.POST)  # Используем CustomAuthenticationForm
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('/')
    else:
        form = CustomAuthenticationForm()  # Используем CustomAuthenticationForm для GET-запроса
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('/')

