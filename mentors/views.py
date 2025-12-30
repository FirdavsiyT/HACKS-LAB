from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from pages.models import Challenge, Solve
from users.models import User
from .forms import ChallengeForm


# Проверка прав доступа
def is_mentor(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Mentors').exists())


@login_required
@user_passes_test(is_mentor, login_url='dashboard')
def dashboard(request):
    total_users = User.objects.count()
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


@login_required
@user_passes_test(is_mentor, login_url='dashboard')
def challenges_list(request):
    challenges = Challenge.objects.select_related('category').order_by('-id')
    return render(request, 'mentors/challenges_list.html', {'challenges': challenges})


@login_required
@user_passes_test(is_mentor, login_url='dashboard')
def challenge_create(request):
    if request.method == 'POST':
        form = ChallengeForm(request.POST)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.author = request.user
            challenge.save()
            messages.success(request, 'Challenge created successfully!')
            return redirect('mentors:challenges_list')
    else:
        form = ChallengeForm()

    return render(request, 'mentors/challenge_form.html', {'form': form, 'title': 'Create Challenge'})


@login_required
@user_passes_test(is_mentor, login_url='dashboard')
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
@user_passes_test(is_mentor, login_url='dashboard')
def challenge_delete(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    if request.method == 'POST':
        challenge.delete()
        messages.success(request, 'Challenge deleted!')
        return redirect('mentors:challenges_list')
    return render(request, 'mentors/challenge_confirm_delete.html', {'challenge': challenge})