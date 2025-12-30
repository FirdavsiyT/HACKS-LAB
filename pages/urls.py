from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('challenges/', views.challenges_view, name='challenges'),
    path('scoreboard/', views.scoreboard, name='scoreboard'),
    path('api/submit_flag/', views.submit_flag, name='submit_flag'),
]