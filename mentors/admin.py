from django.contrib import admin
from .models import LessonSettings


@admin.register(LessonSettings)
class LessonSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'end_time', 'hard_deadline', 'status_display')
    readonly_fields = ('status_display',)

    def status_display(self, obj):
        if obj.is_lesson_active():
            return "✅ Lesson Active"
        if not obj.is_hard_deadline_passed():
            return "⚠️ Overtime (Soft Deadline)"
        return "⛔ Locked (Hard Deadline)"

    status_display.short_description = "Current Status"

    # Запрещаем создавать больше одной записи (так как настройки глобальные)
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)