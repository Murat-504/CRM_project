from django.contrib.auth import views as auth_views, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import path
from django import forms as dj_forms
from apps.accounts.models import CustomUser


# ── Forms ─────────────────────────────────────────────────────────────────────

class LoginForm(dj_forms.Form):
    username = dj_forms.CharField(
        label='Логин',
        widget=dj_forms.TextInput(attrs={'class': 'form-control', 'autofocus': True})
    )
    password = dj_forms.CharField(
        label='Пароль',
        widget=dj_forms.PasswordInput(attrs={'class': 'form-control'})
    )


class ProfileForm(dj_forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'department', 'bio', 'avatar']
        widgets = {
            'first_name': dj_forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  dj_forms.TextInput(attrs={'class': 'form-control'}),
            'email':      dj_forms.EmailInput(attrs={'class': 'form-control'}),
            'phone':      dj_forms.TextInput(attrs={'class': 'form-control'}),
            'department': dj_forms.TextInput(attrs={'class': 'form-control'}),
            'bio':        dj_forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ── Views ─────────────────────────────────────────────────────────────────────

class CRMLoginView(auth_views.LoginView):
    template_name = 'accounts/login.html'
    authentication_form = auth_views.AuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['title'] = 'Вход в CRM'
        return ctx


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            from django.contrib import messages
            messages.success(request, 'Профиль обновлён')
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('accounts:login')


# ── URLs ──────────────────────────────────────────────────────────────────────
app_name = 'accounts'

urlpatterns = [
    path('login/', CRMLoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    path('profile/', profile_view, name='profile'),
]
