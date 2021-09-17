from django.shortcuts import redirect, render

from django.contrib.auth import authenticate, login, logout

from django.contrib import messages

from .forms import CustomUserCreationForm


def login_view(request):
    if request.user.is_authenticated:
        return redirect('autofill:dashboard')
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Successfully login as {email}')
            return redirect('autofill:dashboard')
        else:
            messages.warning(request, 'Email or wrong password')
    return render(request, 'users/login.html')


def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Succesfully logout')
        return redirect('users:login')
    return render(request, 'users/logout.html')


def register_view(request):
    form = CustomUserCreationForm()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            email = form.cleaned_data['email']
            raw_password = form.cleaned_data['password1']
            user = authenticate(email=email, password=raw_password)
            login(request, user)
            messages.success(request, f'Successfully Register with email {email}')
            return redirect('autofill:dashboard')
            
    context = {
        'form': form
    }
    return render(request, 'users/register.html', context)