from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from pages import views as pages_views
from users import views as users_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication
    # ИСПРАВЛЕНО: Указываем users/login.html, так как ваш файл лежит там
    path('accounts/login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', users_views.register, name='register'),
    path('avatar-setup/', users_views.avatar_setup, name='avatar_setup'),

    # Pages
    path('', pages_views.dashboard, name='dashboard'),
    path('challenges/', pages_views.challenges_view, name='challenges'),
    path('scoreboard/', pages_views.scoreboard, name='scoreboard'),

    # API
    path('api/submit_flag/', pages_views.submit_flag, name='submit_flag'),

    # Users
    path('profile/', users_views.profile, name='profile'),

    path('mentor/', include('mentors.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)