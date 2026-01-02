from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Sum, Count, Min, Q
from django.db.models.functions import TruncDate, Coalesce
from .models import Challenge, Category, Solve, Attempt
from users.models import User
from mentors.models import LessonSettings
import json
from collections import defaultdict
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder


def home(request):
    """
    Main Landing Page.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


@login_required
def dashboard(request):
    user_solves = Solve.objects.filter(user=request.user)
    owned_flags = user_solves.count()

    # Only active challenges
    total_flags = Challenge.objects.filter(is_active=True).count()

    # 1. Personal Solves
    solves_qs = Solve.objects.filter(user=request.user).select_related(
        'user', 'challenge', 'challenge__category'
    ).order_by('-date')[:20]

    # 2. Personal Attempts
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

    # 3. Combine lists
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

    # Check for mentor/admin
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

    # Check Timer
    lesson_settings = LessonSettings.get_settings()
    is_hard_deadline = lesson_settings.is_hard_deadline_passed()

    # Pass deadline timestamps for JS countdown
    hard_deadline_iso = None
    if lesson_settings.hard_deadline:
        hard_deadline_iso = lesson_settings.hard_deadline.isoformat()

    soft_deadline_iso = None
    # FIX: Use end_time (model field) instead of soft_deadline
    if lesson_settings.end_time:
        soft_deadline_iso = lesson_settings.end_time.isoformat()

    categories_data = {}
    for cat in categories_qs:
        categories_data[cat.name] = {
            'name': cat.name,
            'icon': 'folder'
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

        # If hard deadline passed and not solved, mark as failed (locked)
        if is_hard_deadline and not is_solved:
            is_failed = True

        c_dict = {
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
        }
        c_dict['json_data'] = json.dumps(c_dict, cls=DjangoJSONEncoder)
        challenges_data.append(c_dict)

    context = {
        'categories': categories_qs,
        'categories_json': json.dumps(categories_data),
        'challenges_data': challenges_data,
        'is_hard_deadline': is_hard_deadline,
        'hard_deadline_iso': hard_deadline_iso,
        'soft_deadline_iso': soft_deadline_iso,  # Now correctly populated from end_time
    }
    return render(request, 'challenges.html', context)


@login_required
def scoreboard(request):
    # Filter: exclude superusers and mentors
    student_users = User.objects.filter(is_superuser=False).exclude(groups__name='Mentors')

    # 1. Top 10 for chart
    top_users_qs = student_users.annotate(
        total_points=Coalesce(Sum('solves__challenge__points'), 0),
        flags_count=Count('solves')
    ).filter(total_points__gt=0).order_by('-total_points', '-flags_count')[:10]

    top_users_list = list(top_users_qs)

    # Add current user to chart if not in top 10
    is_current_user_student = not request.user.is_superuser and not request.user.groups.filter(name='Mentors').exists()

    if is_current_user_student and request.user.is_authenticated and request.user not in top_users_list:
        current_user_points = Solve.objects.filter(user=request.user).aggregate(
            total=Coalesce(Sum('challenge__points'), 0)
        )['total']

        if current_user_points > 0:
            top_users_list.append(request.user)

    # 2. Top 50 list
    all_users_qs = student_users.annotate(
        total_points=Coalesce(Sum('solves__challenge__points'), 0),
        flags_count=Count('solves')
    ).filter(total_points__gt=0).order_by('-total_points', '-flags_count')[:50]

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

    first_solve_ever = Solve.objects.filter(user__in=student_users).aggregate(Min('date'))['date__min']
    global_start_time = first_solve_ever if first_solve_ever else timezone.now()

    colors = [
        '#9fef00', '#00d2ff', '#ff0055', '#ffe600', '#aa00ff',
        '#ff6600', '#00ffaa', '#ff00aa', '#0066ff', '#ccff00'
    ]

    for i, user in enumerate(top_users_list):
        solves = Solve.objects.filter(user=user).select_related('challenge').order_by('date')
        if not solves.exists():
            continue

        color = colors[i % len(colors)]
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


@login_required
def challenge_solves_api(request, challenge_id):
    """
    API for live updates.
    """
    challenge = get_object_or_404(Challenge, id=challenge_id)
    if not challenge.is_active:
        return JsonResponse({'solves': []})

    solves = challenge.solves.select_related('user').order_by('-date')
    data = [{
        'user': s.user.username,
        'avatar': s.user.avatar_url,
        'date': s.date.strftime('%Y-%m-%d %H:%M')
    } for s in solves]

    return JsonResponse({'solves': data})


@login_required
def lesson_status_api(request):
    """
    API для проверки статуса урока (таймера) в реальном времени.
    """
    lesson_settings = LessonSettings.get_settings()
    is_hard_deadline = lesson_settings.is_hard_deadline_passed()

    hard_deadline_iso = None
    if lesson_settings.hard_deadline:
        hard_deadline_iso = lesson_settings.hard_deadline.isoformat()

    soft_deadline_iso = None
    # FIX: Use end_time (model field) instead of soft_deadline
    if lesson_settings.end_time:
        soft_deadline_iso = lesson_settings.end_time.isoformat()

    return JsonResponse({
        'is_hard_deadline': is_hard_deadline,
        'hard_deadline': hard_deadline_iso,
        'soft_deadline': soft_deadline_iso  # Correctly populated
    })


@require_POST
@login_required
def submit_flag(request):
    try:
        data = json.loads(request.body)
        challenge_id = data.get('challenge_id')
        flag_input = data.get('flag')

        challenge = get_object_or_404(Challenge, id=challenge_id, is_active=True)

        # Check Timer
        lesson_settings = LessonSettings.get_settings()
        if lesson_settings.is_hard_deadline_passed():
            return JsonResponse(
                {'status': 'error', 'message': 'Lesson time is over! Submissions closed.', 'challenge_failed': True})

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