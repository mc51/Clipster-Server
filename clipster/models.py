from django.db import models


class Clip(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    text = models.TextField(max_length=10000)
    device = models.CharField(max_length=100, blank=True, default="unspecified")

    def __str__(self):
        return f"user: {self.user} text: {self.text} created at: {self.created_at} device: {self.device}"

    class Meta:
        ordering = ("created_at",)
