from django.contrib.auth import login, logout
from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import SignUpForm


def register(request):
    """Handle new user registration and log the user in immediately after."""
    if request.user.is_authenticated:
        return redirect("jobs:dashboard")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect("jobs:dashboard")
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("accounts:login")
