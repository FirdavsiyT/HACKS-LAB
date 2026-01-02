from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('challenges/', views.challenges_view, name='challenges'),
    path('scoreboard/', views.scoreboard, name='scoreboard'),

    # APIs
    path('api/submit_flag/', views.submit_flag, name='submit_flag'),
    path('api/challenge/<int:challenge_id>/solves/', views.challenge_solves_api, name='challenge_solves_api'),
    path('api/scoreboard/', views.scoreboard, name='scoreboard_api'),  # Новый
    path('api/lesson/status/', views.lesson_status_api, name='lesson_status_api'),
]