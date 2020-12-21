from django.db import models


class Clip(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    text = models.TextField(max_length=10000)
    device = models.CharField(max_length=100, blank=True, default="unspecified")

    def __str__(self):
        return f"User: {self.user} Text: {self.text} Created at: {self.created_at} Device: {self.device}"

    class Meta:
        ordering = ("created_at",)
