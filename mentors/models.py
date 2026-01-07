from django.db import models
from django.utils import timezone
from pages.models import Challenge

class LessonSettings(models.Model):
    """
    Global settings for the current lesson/session.
    Usually implies only one record exists.
    """
    start_time = models.DateTimeField(null=True, blank=True, help_text="Time when the lesson started")
    end_time = models.DateTimeField(null=True, blank=True, help_text="Time when the main lesson ends")
    hard_deadline = models.DateTimeField(null=True, blank=True, help_text="Final blocking time (including delay)")

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and LessonSettings.objects.exists():
            self.pk = LessonSettings.objects.first().pk
        super(LessonSettings, self).save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def is_lesson_active(self):
        if not self.end_time:
            return True  # If timer is not set, lesson is active
        return timezone.now() < self.end_time

    def is_hard_deadline_passed(self):
        if not self.hard_deadline:
            # If hard_deadline is not set, rely on end_time
            # If end_time is also not set, then no deadline
            return False if not self.end_time else timezone.now() > self.end_time
        return timezone.now() > self.hard_deadline


class LessonTemplate(models.Model):
    """
    Модель для группировки задач в один урок/шаблон.
    Позволяет быстро включать/выключать набор задач.
    """
    title = models.CharField(max_length=100, verbose_name="Lesson Title")
    description = models.TextField(blank=True, verbose_name="Description")
    challenges = models.ManyToManyField(Challenge, related_name='templates', verbose_name="Challenges")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def challenges_count(self):
        return self.challenges.count()

    @property
    def total_points(self):
        return self.challenges.aggregate(total=models.Sum('points'))['total'] or 0