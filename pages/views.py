from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from .models import Challenge, Category, Solve, Attempt
from users.models import User
import json
from collections import defaultdict
from django.utils import timezone


@login_required
def dashboard(request):
    user_solves = Solve.objects.filter(user=request.user)
    owned_flags = user_solves.count()
    total_flags = Challenge.objects.count()

    # 1. Получаем глобальные решения (Успехи всех)
    solves_qs = Solve.objects.select_related('user', 'challenge', 'challenge__category').order_by('-date')[:20]

    # 2. Получаем ЛИЧНЫЕ провалы
    attempts_qs = Attempt.objects.filter(
        user=request.user,
        is_correct=False,
        challenge__max_attempts__gt=0
    ).select_related('challenge', 'challenge__category').order_by('timestamp')

    grouped_attempts = defaultdict(list)
    for att in attempts_qs:
        grouped_attempts[att.challenge_id].append(att)

    fail_events = []
    for ch_id, attempts in grouped_attempts.items():
        if not attempts: continue

        challenge = attempts[0].challenge
        limit = challenge.max_attempts

        if len(attempts) >= limit:
            locking_attempt = attempts[limit - 1]
            fail_events.append(locking_attempt)

    # 3. Объединяем списки
    activity_list = []

    for s in solves_qs:
        activity_list.append({
            'type': 'solve',
            'user': s.user,
            'challenge': s.challenge,
            'date': s.date,
            'sort_date': s.date
        })

    for f in fail_events:
        activity_list.append({
            'type': 'fail',
            'user': f.user,
            'challenge': f.challenge,
            'date': f.timestamp,
            'sort_date': f.timestamp
        })

    activity_log = sorted(activity_list, key=lambda x: x['sort_date'], reverse=True)[:10]

    context = {
        'owned_flags': owned_flags,
        'total_flags': total_flags,
        'activity_log': activity_log,
        'progress_percent': int((owned_flags / total_flags * 100)) if total_flags > 0 else 0
    }
    return render(request, 'dashboard.html', context)


@login_required
def challenges_view(request):
    challenges = Challenge.objects.select_related('category').all()
    categories_qs = Category.objects.all()

    categories_data = {}
    for cat in categories_qs:
        icon = 'folder'

        categories_data[cat.name] = {
            'name': cat.name,
            'icon': icon
        }

    user_solves_ids = set(Solve.objects.filter(user=request.user).values_list('challenge_id', flat=True))

    user_attempts_map = {}
    attempts_qs = Attempt.objects.filter(user=request.user).values('challenge_id').annotate(count=Count('id'))
    for item in attempts_qs:
        user_attempts_map[item['challenge_id']] = item['count']

    challenges_data = []
    for c in challenges:
        solves_list = [{
            'user': s.user.username,
            'avatar': s.user.avatar_url,
            'date': s.date.strftime('%Y-%m-%d %H:%M')
        } for s in c.solves.select_related('user').order_by('-date')[:5]]

        is_solved = c.id in user_solves_ids
        attempts_count = user_attempts_map.get(c.id, 0)

        is_failed = False
        if c.max_attempts > 0 and attempts_count >= c.max_attempts and not is_solved:
            is_failed = True

        challenges_data.append({
            'id': c.id,
            'title': c.title,
            'category': c.category.name,
            'points': c.points,
            'difficulty': c.difficulty,
            'solved': is_solved,
            'failed': is_failed,
            'attempts': attempts_count,
            'max_attempts': c.max_attempts,
            'desc': c.description,
            'author': c.author,
            'solves': solves_list
        })

    context = {
        'categories': categories_qs,
        'categories_json': json.dumps(categories_data),
        'challenges_data': challenges_data
    }
    return render(request, 'challenges.html', context)


@login_required
def scoreboard(request):
    # 1. Получаем ТОП-10 пользователей для графика
    top_users_qs = User.objects.annotate(
        total_points=Sum('solves__challenge__points'),
        flags_count=Count('solves')
    ).order_by('-total_points', '-flags_count')[:10]

    top_users_list = list(top_users_qs)

    # 2. Получаем ПОЛНЫЙ список для таблицы (топ-50)
    all_users_qs = User.objects.annotate(
        total_points=Sum('solves__challenge__points'),
        flags_count=Count('solves')
    ).order_by('-total_points', '-flags_count')[:50]

    leaderboard_data = []
    for index, u in enumerate(all_users_qs, 1):
        leaderboard_data.append({
            'rank': index,
            'user': u.username,
            'points': u.total_points or 0,
            'solved': u.flags_count,
            'isMe': u == request.user,
            'avatar': u.avatar_url
        })

    # 3. Подготовка данных для графика (Relative Time vs Score)
    graph_data = {
        'datasets': []
    }

    colors = [
        '#9fef00', '#00d2ff', '#ff0055', '#ffe600', '#aa00ff',
        '#ff6600', '#00ffaa', '#ff00aa', '#0066ff', '#ccff00'
    ]

    for i, user in enumerate(top_users_list):
        solves = Solve.objects.filter(user=user).select_related('challenge').order_by('date')

        if not solves.exists():
            continue

        # Определяем время старта (первое решение)
        start_time = solves[0].date

        # Первая точка: 0 часов, 0 очков
        data_points = [{'x': 0, 'y': 0}]
        current_score = 0

        for solve in solves:
            current_score += solve.challenge.points

            # Вычисляем, сколько часов прошло с момента старта
            time_delta = solve.date - start_time
            hours_elapsed = round(time_delta.total_seconds() / 3600, 2)  # Часы с сотыми долями

            data_points.append({'x': hours_elapsed, 'y': current_score})

        graph_data['datasets'].append({
            'label': user.username,
            'data': data_points,
            'borderColor': colors[i % len(colors)],
            'backgroundColor': 'transparent',
            'borderWidth': 2,
            'tension': 0.2,  # Легкое сглаживание
            'pointRadius': 3,
            'pointHoverRadius': 6,
            'showLine': True
        })

    # Примечание: Для Chart.js при использовании объектов {x, y} метки labels не обязательны,
    # график автоматически построит линейную ось X.

    context = {
        'leaderboard_data': leaderboard_data,
        'graph_data_json': json.dumps(graph_data)
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

        attempts_count = Attempt.objects.filter(user=request.user, challenge=challenge).count()

        if challenge.max_attempts > 0 and attempts_count >= challenge.max_attempts:
            return JsonResponse(
                {'status': 'error', 'message': 'Max attempts reached! Task locked.', 'challenge_failed': True})

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
            new_attempts_count = attempts_count + 1
            challenge_failed = False
            message = 'Incorrect flag'

            if challenge.max_attempts > 0 and new_attempts_count >= challenge.max_attempts:
                challenge_failed = True
                message = 'Incorrect flag. Max attempts reached. Task locked.'

            return JsonResponse({
                'status': 'error',
                'message': message,
                'challenge_failed': challenge_failed
            })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)