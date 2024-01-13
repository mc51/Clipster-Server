from django.db import models
from django.conf import settings


class Clip(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    text = models.TextField(max_length=settings.MAX_CLIP_LENGTH)
    format = models.CharField(max_length=3, blank=True, default="txt")
    device = models.CharField(max_length=100, blank=True, default="unspecified")

    def __str__(self):
        return f"user: {self.user} format: {self.format} text: {self.text} created at: {self.created_at} device: {self.device}"

    class Meta:
        ordering = ("created_at",)
