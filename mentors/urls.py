from django.urls import path
from . import views

app_name = 'mentors'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('challenges/', views.challenges_list, name='challenges_list'),
    path('challenges/new/', views.challenge_create, name='challenge_create'),
    path('challenges/<int:pk>/edit/', views.challenge_edit, name='challenge_edit'),
    path('challenges/<int:pk>/delete/', views.challenge_delete, name='challenge_delete'),
]