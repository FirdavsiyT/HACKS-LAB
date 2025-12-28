from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.db.models import Sum
from .models import User


@login_required(login_url='/admin/login/')
def profile(request):
    if request.method == 'POST':
        # Здесь можно добавить логику обработки формы смены пароля/email
        pass

    score = request.user.score
    # Исправлено: используем 'solves' вместо 'solve_set'
    flags_count = request.user.solves.count()

    # Расчет ранга
    # Считаем, сколько юзеров имеют больше очков
    # Исправлено: используем 'solves__challenge__points'
    users_above = User.objects.annotate(tp=Sum('solves__challenge__points')).filter(tp__gt=score).count()
    rank = users_above + 1

    context = {
        'score': score,
        'flags_count': flags_count,
        'rank': rank,
        'accuracy': '100%'
    }
    return render(request, 'users/profile.html', context)