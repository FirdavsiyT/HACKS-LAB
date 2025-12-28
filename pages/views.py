from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count
from .models import Challenge, Category, Solve, Attempt
from users.models import User
import json


@login_required(login_url='/admin/login/')
def dashboard(request):
    user_solves = Solve.objects.filter(user=request.user)
    owned_flags = user_solves.count()
    total_flags = Challenge.objects.count()

    activity_log = Solve.objects.select_related('user', 'challenge', 'challenge__category').order_by('-date')[:10]

    context = {
        'owned_flags': owned_flags,
        'total_flags': total_flags,
        'activity_log': activity_log,
        'progress_percent': int((owned_flags / total_flags * 100)) if total_flags > 0 else 0
    }
    return render(request, 'dashboard.html', context)


@login_required(login_url='/admin/login/')
def challenges_view(request):
    challenges = Challenge.objects.select_related('category').all()
    categories_qs = Category.objects.all()

    # Формируем метаданные категорий для JS (имя и иконка)
    # Так как иконок в БД нет, подбираем их тут или ставим дефолт
    categories_data = {}
    for cat in categories_qs:
        icon = 'flag'  # Дефолтная иконка
        name_lower = cat.name.lower()
        if 'web' in name_lower:
            icon = 'globe'
        elif 'crypto' in name_lower:
            icon = 'lock'
        elif 'pwn' in name_lower or 'binary' in name_lower:
            icon = 'cpu'
        elif 'reverse' in name_lower:
            icon = 'code'

        categories_data[cat.name] = {
            'name': cat.name,
            'icon': icon
        }

    user_solves_ids = set(Solve.objects.filter(user=request.user).values_list('challenge_id', flat=True))

    challenges_data = []
    for c in challenges:
        solves_list = [{
            'user': s.user.username,
            'date': s.date.strftime('%Y-%m-%d %H:%M')
        } for s in c.solves.select_related('user').order_by('-date')[:5]]

        challenges_data.append({
            'id': c.id,
            'title': c.title,
            # Используем имя категории вместо slug
            'category': c.category.name,
            'points': c.points,
            'difficulty': c.difficulty,
            'solved': c.id in user_solves_ids,
            'desc': c.description,
            'author': c.author,
            'solves': solves_list
        })

    context = {
        'categories': categories_qs,
        # Обязательно передаем JSON с категориями, чтобы не было ошибки в JS
        'categories_json': json.dumps(categories_data),
        'challenges_data': challenges_data
    }
    return render(request, 'challenges.html', context)


@login_required(login_url='/admin/login/')
def scoreboard(request):
    # Исправлено: используем 'solves' вместо 'solve', так как добавили related_name='solves'
    users = User.objects.annotate(
        total_points=Sum('solves__challenge__points'),
        flags_count=Count('solves')
    ).order_by('-total_points', '-flags_count')[:50]

    leaderboard_data = []
    for index, u in enumerate(users, 1):
        leaderboard_data.append({
            'rank': index,
            'user': u.username,
            'points': u.total_points or 0,
            'solved': u.flags_count,
            'isMe': u == request.user,
            'avatar': u.avatar_url
        })

    context = {
        'leaderboard_data': leaderboard_data
    }
    return render(request, 'scoreboard.html', context)


@require_POST
@login_required
def submit_flag(request):
    try:
        data = json.loads(request.body)
        challenge_id = data.get('challenge_id')
        flag_input = data.get('flag')

        challenge = get_object_or_404(Challenge, id=challenge_id)

        if challenge.max_attempts > 0:
            attempts_count = Attempt.objects.filter(user=request.user, challenge=challenge).count()
            if attempts_count >= challenge.max_attempts:
                return JsonResponse({'status': 'error', 'message': 'Max attempts reached!'})

        if Solve.objects.filter(user=request.user, challenge=challenge).exists():
            return JsonResponse({'status': 'error', 'message': 'Already solved!'})

        is_correct = (flag_input == challenge.flag)

        Attempt.objects.create(
            user=request.user,
            challenge=challenge,
            flag_input=flag_input,
            is_correct=is_correct
        )

        if is_correct:
            Solve.objects.create(user=request.user, challenge=challenge)
            return JsonResponse({'status': 'success', 'message': 'Correct flag!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Incorrect flag'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)