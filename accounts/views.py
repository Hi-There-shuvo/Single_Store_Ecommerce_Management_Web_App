from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings

from .forms import CustomUserCreationForm, ForgotPasswordForm, SetNewPasswordForm, UserUpdateForm, ProfileUpdateForm


# ─── Helper: Build absolute URL ──────────────────────────────────────

def _build_absolute_url(request, path):
    """Build a full URL from a relative path."""
    return f"{request.scheme}://{request.get_host()}{path}"


# ─── Registration with Email Verification ─────────────────────────────

def register(request):
    """User registration — automatically activates and logs the user in."""
    if request.user.is_authenticated:
        return redirect('store:home')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # Saves and keeps active (is_active=True by default)
            login(request, user)  # Auto-login immediately
            messages.success(request, f"Welcome to SoloStore, {user.username}! Your account has been created successfully.")
            return redirect('store:home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


def _send_verification_email(request, user):
    """Send an activation link to the user's email."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    activation_url = _build_absolute_url(
        request, f"/accounts/activate/{uid}/{token}/"
    )
    subject = f"Verify your email — {getattr(settings, 'DEFAULT_FROM_EMAIL', 'SoloStore')}"
    message = render_to_string('accounts/emails/verification_email.html', {
        'user': user,
        'activation_url': activation_url,
    })
    send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)


def activate(request, uidb64, token):
    """Activate user account via email verification link."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return render(request, 'accounts/activation_success.html')
    else:
        return render(request, 'accounts/activation_failed.html')


# ─── Login ────────────────────────────────────────────────────────────

def user_login(request):
    """User login view — checks if account is verified."""
    if request.user.is_authenticated:
        return redirect('store:home')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            # Handle 'next' parameter — it's a URL path, not a URL name
            next_url = request.GET.get('next') or request.POST.get('next', '')
            if next_url:
                return redirect(next_url)
            return redirect('store:home')
        else:
            # Check if the user exists but is inactive (unverified email)
            username = request.POST.get('username', '')
            try:
                existing_user = User.objects.get(username=username)
                if not existing_user.is_active:
                    messages.error(request, 'Your account is deactivated. Please contact support.')
                else:
                    messages.error(request, 'Invalid username or password.')
            except User.DoesNotExist:
                messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})


# ─── Logout ───────────────────────────────────────────────────────────

@login_required
def user_logout(request):
    """User logout view."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('store:home')


# ─── Profile ──────────────────────────────────────────────────────────

@login_required
def profile(request):
    """User profile - shows account info, order history link, and update forms."""
    user = request.user
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('accounts:profile')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileUpdateForm(instance=user.profile)

    return render(request, 'accounts/profile.html', {
        'user': user,
        'user_form': user_form,
        'profile_form': profile_form,
    })



# ─── Forgot Password ─────────────────────────────────────────────────

def forgot_password(request):
    """Forgot password — sends a reset link to the user's email."""
    if request.user.is_authenticated:
        return redirect('store:home')
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            users = User.objects.filter(email=email, is_active=True)
            for user in users:
                _send_password_reset_email(request, user)
            # Always show success (security: don't reveal if email exists)
            return render(request, 'accounts/password_reset_sent.html', {'email': email})
    else:
        form = ForgotPasswordForm()
    return render(request, 'accounts/forgot_password.html', {'form': form})


def _send_password_reset_email(request, user):
    """Send a password reset link to the user's email."""
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    reset_url = _build_absolute_url(
        request, f"/accounts/reset-password/{uid}/{token}/"
    )
    subject = f"Reset your password — {getattr(settings, 'DEFAULT_FROM_EMAIL', 'SoloStore')}"
    message = render_to_string('accounts/emails/password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
    })
    send_mail(subject, '', settings.DEFAULT_FROM_EMAIL, [user.email], html_message=message)


def reset_password(request, uidb64, token):
    """Reset password via email link."""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is None or not default_token_generator.check_token(user, token):
        return render(request, 'accounts/activation_failed.html', {
            'title': 'Invalid Reset Link',
            'message': 'This password reset link is invalid or has expired.',
        })

    if request.method == 'POST':
        form = SetNewPasswordForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data['new_password1'])
            user.save()
            return render(request, 'accounts/password_reset_done.html')
    else:
        form = SetNewPasswordForm()
    return render(request, 'accounts/password_reset_form.html', {
        'form': form, 'uidb64': uidb64, 'token': token,
    })
