from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db.models import Sum


class User(AbstractUser):
    avatar_url = models.CharField(
        max_length=255,
        default="https://api.dicebear.com/7.x/bottts/svg?seed=default",
        verbose_name="Аватар"
    )
    # Эти поля используются в admin.py, их нужно добавить в модель
    bio = models.TextField(verbose_name="О себе", blank=True, null=True)
    country = models.CharField(max_length=50, verbose_name="Страна", blank=True, null=True)

    # Исправление конфликтов reverse accessors
    groups = models.ManyToManyField(
        Group,
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="custom_user_set",  # Уникальное имя обратной связи
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="custom_user_set",  # Уникальное имя обратной связи
        related_query_name="user",
    )

    @property
    def score(self):
        # ИСПРАВЛЕНО: Используем 'solves' (как указано в related_name модели Solve в pages/models.py)
        # вместо 'solve_set' (стандартное Django имя, которое было переопределено)
        total = self.solves.aggregate(total=Sum('challenge__points'))['total']
        return total if total is not None else 0

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"