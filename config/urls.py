from django.conf.urls.static import static
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

# --- Custom Error Handlers ---
def custom_page_not_found_view(request, exception):
    return render(request, "errors/404.html", status=404)

def custom_error_view(request):
    return render(request, "errors/500.html", status=500)

def custom_permission_denied_view(request, exception):
    return render(request, "errors/403.html", status=403)

def custom_bad_request_view(request, exception):
    return render(request, "errors/400.html", status=400)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('users/', include('users.urls')),
    path('mentors/', include('mentors.urls')),
    path('summernote/', include('django_summernote.urls')),
]
# Указываем Django использовать наши кастомные view для обработки ошибок
handler404 = 'config.urls.custom_page_not_found_view'
handler500 = 'config.urls.custom_error_view'
handler403 = 'config.urls.custom_permission_denied_view'
handler400 = 'config.urls.custom_bad_request_view'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)