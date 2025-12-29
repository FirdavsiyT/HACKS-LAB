from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, login
from django.contrib import messages
from django.db.models import Sum
from .models import User
from .forms import CustomUserCreationForm
from pages.models import Attempt


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to HACKLABS.')
            return redirect('avatar_setup')
    else:
        form = CustomUserCreationForm()

    return render(request, 'users/register.html', {'form': form})


@login_required
def avatar_setup(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save':
            avatar_url = request.POST.get('avatar_url')
            if avatar_url:
                request.user.avatar_url = avatar_url
                request.user.save()
                messages.success(request, 'Avatar setup complete!')
        else:
            messages.info(request, 'Avatar setup skipped. Default avatar applied.')

        return redirect('dashboard')

    return render(request, 'users/avatar_setup.html')


@login_required
def profile(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_email':
            email = request.POST.get('email')
            password = request.POST.get('password')

            if not email or not password:
                messages.error(request, 'All fields are required')
            elif request.user.check_password(password):
                if User.objects.filter(email=email).exclude(pk=request.user.pk).exists():
                    messages.error(request, 'Email is already in use')
                else:
                    request.user.email = email
                    request.user.save()
                    messages.success(request, 'Email successfully updated')
            else:
                messages.error(request, 'Incorrect password')

        elif action == 'update_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')

            if not current_password or not new_password:
                messages.error(request, 'All fields are required')
            elif request.user.check_password(current_password):
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, 'Password successfully updated')
            else:
                messages.error(request, 'Incorrect current password')

        elif action == 'update_avatar':
            avatar_url = request.POST.get('avatar_url')
            if avatar_url:
                request.user.avatar_url = avatar_url
                request.user.save()
                messages.success(request, 'Avatar updated!')

        return redirect('profile')

    score = request.user.score
    flags_count = request.user.solves.count()

    users_with_points = User.objects.annotate(
        total_points=Sum('solves__challenge__points')
    )
    current_points = score
    users_above = users_with_points.filter(total_points__gt=current_points).count()
    rank = users_above + 1

    total_attempts = Attempt.objects.filter(user=request.user).count()
    if total_attempts > 0:
        accuracy_val = (flags_count / total_attempts) * 100
        accuracy = f"{accuracy_val:.1f}%"
    else:
        accuracy = "0%" if flags_count == 0 else "100%"

    context = {
        'score': score,
        'flags_count': flags_count,
        'rank': rank,
        'accuracy': accuracy
    }
    return render(request, 'users/profile.html', context)