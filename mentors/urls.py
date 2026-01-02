from django.urls import path
from . import views

app_name = 'mentors'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Challenges
    path('challenges/', views.challenges_list, name='challenges_list'),
    path('challenges/new/', views.challenge_create, name='challenge_create'),
    path('challenges/bulk_action/', views.bulk_challenges_action, name='bulk_challenges_action'),
    path('challenges/disable_all/', views.disable_all_challenges, name='disable_all_challenges'),
    path('challenges/export/docx/', views.export_challenges_docx, name='export_challenges_docx'), # <-- NEW DOCX EXPORT

    path('challenges/<int:pk>/edit/', views.challenge_edit, name='challenge_edit'),
    path('challenges/<int:pk>/delete/', views.challenge_delete, name='challenge_delete'),
    path('challenges/<int:pk>/toggle/', views.challenge_toggle_active, name='challenge_toggle'),

    # Categories
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/new/', views.category_create, name='category_create'),
    path('categories/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # Users & System Control
    path('users/', views.users_list, name='users_list'),
    path('users/export/', views.export_users_csv, name='export_users_csv'),
    path('system/reset/', views.reset_platform, name='reset_platform'),
]