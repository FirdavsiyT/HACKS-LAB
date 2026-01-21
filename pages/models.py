from django.db import models
from django.conf import settings

class Category(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Challenge(models.Model):
    DIFFICULTY_CHOICES = [
        ('Easy', 'Easy'),
        ('Medium', 'Medium'),
        ('Hard', 'Hard'),
        ('Insane', 'Insane'),
    ]

    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='challenges')
    description = models.TextField()
    points = models.IntegerField(default=100)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Easy')
    flag = models.CharField(max_length=200)
    author = models.CharField(max_length=100, default="Admin")
    max_attempts = models.PositiveIntegerField(default=0, help_text="0 = infinity")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.title} ({self.points})"


class Solve(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='solves')
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='solves')
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'challenge')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} -> {self.challenge.title}"


class Attempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    flag_input = models.CharField(max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']