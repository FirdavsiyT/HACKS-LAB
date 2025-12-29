from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.db.models import Sum
from .models import User
# Импортируем Attempt для расчета точности
from pages.models import Attempt


@login_required(login_url='/accounts/login/')
def profile(request):
    # ИСПРАВЛЕНО: Реализована логика смены пароля и email
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_email':
            email = request.POST.get('email')
            password = request.POST.get('password')
            # Проверяем пароль перед сменой email
            if request.user.check_password(password):
                request.user.email = email
                request.user.save()
                messages.success(request, 'Email successfully updated')
            else:
                messages.error(request, 'Incorrect password')

        elif action == 'update_password':
            current_password = request.POST.get('current_password')
            new_password = request.POST.get('new_password')
            # Проверяем старый пароль
            if request.user.check_password(current_password):
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)  # Чтобы пользователя не разлогинило
                messages.success(request, 'Password successfully updated')
            else:
                messages.error(request, 'Incorrect current password')

        return redirect('profile')

    score = request.user.score
    flags_count = request.user.solves.count()

    # Расчет ранга
    # Считаем сумму очков для всех пользователей, чтобы корректно сравнить
    users_with_points = User.objects.annotate(
        total_points=Sum('solves__challenge__points')
    )

    # Получаем текущие очки (если None, то 0)
    current_points = score

    # Считаем, у скольких пользователей очков БОЛЬШЕ, чем у текущего
    users_above = users_with_points.filter(total_points__gt=current_points).count()
    rank = users_above + 1

    # ИСПРАВЛЕНО: Расчет реальной точности (Accuracy)
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