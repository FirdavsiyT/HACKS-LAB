from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Min, Q
from django.db.models.functions import TruncDate, Coalesce
from .models import Challenge, Category, Solve, Attempt
from users.models import User
import json
from collections import defaultdict
from django.utils import timezone


def home(request):
    """
    Главная страница (Landing Page).
    Если пользователь авторизован -> редирект на Dashboard.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    user_solves = Solve.objects.filter(user=request.user)
    owned_flags = user_solves.count()

    # Считаем только АКТИВНЫЕ задачи в общем количестве
    total_flags = Challenge.objects.filter(is_active=True).count()

    # 1. Получаем ЛИЧНЫЕ решения
    solves_qs = Solve.objects.filter(user=request.user).select_related('user', 'challenge',
                                                                       'challenge__category').order_by('-date')[:20]

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

    # Проверка на ментора/админа для уведомления
    is_mentor = request.user.is_superuser or request.user.groups.filter(name='Mentors').exists()

    context = {
        'owned_flags': owned_flags,
        'total_flags': total_flags,
        'activity_log': activity_log,
        'progress_percent': int((owned_flags / total_flags * 100)) if total_flags > 0 else 0,
        'is_mentor': is_mentor,
    }
    return render(request, 'dashboard.html', context)


@login_required
def challenges_view(request):
    challenges = Challenge.objects.filter(is_active=True).select_related('category')
    categories_qs = Category.objects.filter(challenges__is_active=True).distinct()

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
        } for s in c.solves.select_related('user').order_by('-date')]

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
    top_users_qs = User.objects.annotate(
        total_points=Coalesce(Sum('solves__challenge__points'), 0),
        flags_count=Count('solves')
    ).order_by('-total_points', '-flags_count')[:10]

    top_users_list = list(top_users_qs)

    if request.user.is_authenticated and request.user not in top_users_list:
        top_users_list.append(request.user)

    all_users_qs = User.objects.annotate(
        total_points=Coalesce(Sum('solves__challenge__points'), 0),
        flags_count=Count('solves')
    ).order_by('-total_points', '-flags_count')[:50]

    leaderboard_data = []
    for index, u in enumerate(all_users_qs, 1):
        leaderboard_data.append({
            'rank': index,
            'user': u.username,
            'points': u.total_points,
            'solved': u.flags_count,
            'isMe': u == request.user,
            'avatar': u.avatar_url
        })

    graph_data = {'datasets': []}
    first_solve_ever = Solve.objects.aggregate(Min('date'))['date__min']
    global_start_time = first_solve_ever if first_solve_ever else timezone.now()

    colors = [
        '#9fef00', '#00d2ff', '#ff0055', '#ffe600', '#aa00ff',
        '#ff6600', '#00ffaa', '#ff00aa', '#0066ff', '#ccff00'
    ]

    for i, user in enumerate(top_users_list):
        solves = Solve.objects.filter(user=user).select_related('challenge').order_by('date')
        color = colors[i % len(colors)]

        if not solves.exists():
            graph_data['datasets'].append({
                'label': user.username,
                'data': [{'x': 0, 'y': 0}],
                'borderColor': color,
                'backgroundColor': 'transparent',
                'borderWidth': 2,
                'tension': 0,
                'pointRadius': 0,
                'stepped': 'after'
            })
            continue

        data_points = [{'x': 0, 'y': 0}]
        current_score = 0

        for solve in solves:
            current_score += solve.challenge.points
            time_delta = solve.date - global_start_time
            seconds_elapsed = int(time_delta.total_seconds())
            if seconds_elapsed < 0: seconds_elapsed = 0
            data_points.append({'x': seconds_elapsed, 'y': current_score})

        now_delta = timezone.now() - global_start_time
        now_seconds = int(now_delta.total_seconds())
        data_points.append({'x': now_seconds, 'y': current_score})

        graph_data['datasets'].append({
            'label': user.username,
            'data': data_points,
            'borderColor': color,
            'backgroundColor': 'transparent',
            'borderWidth': 2,
            'tension': 0,
            'pointRadius': 3,
            'pointHoverRadius': 6,
            'showLine': True,
            'stepped': 'after'
        })

    context = {
        'leaderboard_data': leaderboard_data,
        'graph_data': graph_data
    }
    return render(request, 'scoreboard.html', context)


@require_POST
@login_required
def submit_flag(request):
    try:
        data = json.loads(request.body)
        challenge_id = data.get('challenge_id')
        flag_input = data.get('flag')

        challenge = get_object_or_404(Challenge, id=challenge_id, is_active=True)

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