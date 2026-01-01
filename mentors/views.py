import csv
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.db import transaction
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from pages.models import Challenge, Solve, Category, Attempt
from users.models import User
from .forms import ChallengeForm, CategoryForm


# --- Custom Decorator ---
def mentor_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_superuser or request.user.groups.filter(name='Mentors').exists():
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return _wrapped_view


# --- VIEWS ---

@login_required
@mentor_required
def dashboard(request):
    total_users = User.objects.filter(is_superuser=False).count()
    total_challenges = Challenge.objects.count()
    total_solves = Solve.objects.count()

    recent_solves = Solve.objects.select_related('user', 'challenge').order_by('-date')[:10]

    context = {
        'total_users': total_users,
        'total_challenges': total_challenges,
        'total_solves': total_solves,
        'recent_solves': recent_solves,
    }
    return render(request, 'mentors/dashboard.html', context)


# --- CHALLENGES ---

@login_required
@mentor_required
def challenges_list(request):
    sort_by = request.GET.get('sort', 'newest')
    category_filter = request.GET.get('category')

    challenges = Challenge.objects.select_related('category')

    if category_filter:
        challenges = challenges.filter(category__name=category_filter)

    if sort_by == 'category':
        challenges = challenges.order_by('category__name', 'title')
    elif sort_by == 'points_asc':
        challenges = challenges.order_by('points')
    elif sort_by == 'points_desc':
        challenges = challenges.order_by('-points')
    elif sort_by == 'active':
        challenges = challenges.order_by('-is_active', '-id')
    elif sort_by == 'inactive':
        challenges = challenges.order_by('is_active', '-id')
    else:
        challenges = challenges.order_by('-id')

    categories = Category.objects.all().order_by('name')

    context = {
        'challenges': challenges,
        'categories': categories,
        'current_sort': sort_by,
        'current_category': category_filter
    }
    return render(request, 'mentors/challenges_list.html', context)


@login_required
@mentor_required
@require_POST
def bulk_challenges_action(request):
    action = request.POST.get('action')
    challenge_ids = request.POST.getlist('challenge_ids')

    if not challenge_ids:
        messages.warning(request, 'No challenges selected.')
        return redirect('mentors:challenges_list')

    if action == 'enable_selected':
        count = Challenge.objects.filter(id__in=challenge_ids).update(is_active=True)
        messages.success(request, f'Enabled {count} challenges.')
    elif action == 'disable_selected':
        count = Challenge.objects.filter(id__in=challenge_ids).update(is_active=False)
        messages.success(request, f'Disabled {count} challenges.')

    return redirect('mentors:challenges_list')


@login_required
@mentor_required
def challenge_create(request):
    if request.method == 'POST':
        form = ChallengeForm(request.POST)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.author = request.user.username
            challenge.save()
            messages.success(request, 'Challenge created successfully!')
            return redirect('mentors:challenges_list')
    else:
        form = ChallengeForm()

    return render(request, 'mentors/challenge_form.html', {'form': form, 'title': 'Create Challenge'})


@login_required
@mentor_required
def challenge_edit(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    if request.method == 'POST':
        form = ChallengeForm(request.POST, instance=challenge)
        if form.is_valid():
            form.save()
            messages.success(request, 'Challenge updated successfully!')
            return redirect('mentors:challenges_list')
    else:
        form = ChallengeForm(instance=challenge)

    return render(request, 'mentors/challenge_form.html', {'form': form, 'title': 'Edit Challenge'})


@login_required
@mentor_required
def challenge_delete(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    if request.method == 'POST':
        challenge.delete()
        messages.success(request, 'Challenge deleted!')
        return redirect('mentors:challenges_list')
    return render(request, 'mentors/challenge_confirm_delete.html', {'object': challenge, 'type': 'Challenge'})


@login_required
@mentor_required
@require_POST
def challenge_toggle_active(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    challenge.is_active = not challenge.is_active
    challenge.save()
    messages.success(request, f'Challenge "{challenge.title}" is now {"Active" if challenge.is_active else "Hidden"}')
    return redirect('mentors:challenges_list')


@login_required
@mentor_required
@require_POST
def disable_all_challenges(request):
    if request.POST.get('confirm') != 'CONFIRM_DISABLE':
        messages.error(request, 'Confirmation failed. Type CONFIRM_DISABLE exactly.')
        return redirect('mentors:challenges_list')

    updated_count = Challenge.objects.update(is_active=False)

    messages.success(request, f'Lockdown initiated! {updated_count} challenges hidden.')
    return redirect('mentors:challenges_list')


# --- CATEGORIES ---

@login_required
@mentor_required
def categories_list(request):
    categories = Category.objects.annotate(challenge_count=Count('challenges')).order_by('name')
    return render(request, 'mentors/categories_list.html', {'categories': categories})


@login_required
@mentor_required
def category_create(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created!')
            return redirect('mentors:categories_list')
    else:
        form = CategoryForm()
    return render(request, 'mentors/category_form.html', {'form': form, 'title': 'Create Category'})


@login_required
@mentor_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated!')
            return redirect('mentors:categories_list')
    else:
        form = CategoryForm(instance=category)
    return render(request, 'mentors/category_form.html', {'form': form, 'title': 'Edit Category'})


@login_required
@mentor_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted!')
        return redirect('mentors:categories_list')
    return render(request, 'mentors/category_confirm_delete.html', {'object': category, 'type': 'Category'})


# --- USERS & SYSTEM ---

@login_required
@mentor_required
def users_list(request):
    users = User.objects.filter(is_superuser=False).annotate(
        total_points=Coalesce(Sum('solves__challenge__points'), 0),
        solved_count=Count('solves')
    ).order_by('-total_points')

    return render(request, 'mentors/users_list.html', {'users': users})


@login_required
@mentor_required
def export_users_csv(request):
    """
    Экспорт результатов всех студентов в CSV файл.
    """
    response = HttpResponse(content_type='text/csv')
    timestamp = timezone.now().strftime('%Y-%m-%d_%H-%M')
    response['Content-Disposition'] = f'attachment; filename="hacklabs_results_{timestamp}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Rank', 'Username', 'Email', 'Total Score', 'Flags Solved', 'Last Login'])

    users = User.objects.filter(is_superuser=False).annotate(
        total_points=Coalesce(Sum('solves__challenge__points'), 0),
        solved_count=Count('solves')
    ).order_by('-total_points')

    for index, user in enumerate(users, 1):
        writer.writerow([
            index,
            user.username,
            user.email,
            user.total_points,
            user.solved_count,
            user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'Never'
        ])

    return response


@login_required
@mentor_required
@require_POST
def reset_platform(request):
    if request.POST.get('confirm') != 'CONFIRM_RESET':
        messages.error(request, 'Confirmation failed. Type CONFIRM_RESET exactly.')
        return redirect('mentors:users_list')

    with transaction.atomic():
        Solve.objects.all().delete()
        Attempt.objects.all().delete()

        # Удаляем студентов, исключая менторов
        deleted_count, _ = User.objects.filter(
            is_superuser=False,
            is_staff=False
        ).exclude(
            groups__name='Mentors'
        ).delete()

        messages.success(request, f'Platform Reset Complete! Removed {deleted_count} users and all progress.')

    return redirect('mentors:users_list')