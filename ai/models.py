from django.conf import settings
from django.db import models


class AICallLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_calls",
    )
    feature_name = models.CharField(max_length=100)
    provider = models.CharField(max_length=50, default="groq")
    model_name = models.CharField(max_length=100)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.000000)
    latency_ms = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.feature_name} by {self.user} ({self.created_at.date()})"
