from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from clipster.models import Clip
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.conf import settings


class ClipSerializer(serializers.ModelSerializer):
    # Using ModelSerializers is just shortcut for Serializers
    # with default create and update
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Clip
        fields = ("id", "user", "text", "device", "created_at")


class UserSerializer(serializers.ModelSerializer):
    # User object: username and hashed password
    def create(self, valid_data):
        User = get_user_model()
        user = User(username=valid_data["username"])
        user.set_password(valid_data["password"])
        user.save()
        return user

    class Meta:
        User = get_user_model()
        model = User
        # extra_kwargs = {'password': {'write_only': True}}
        fields = ("id", "username", "password")


@receiver(post_save, sender=Clip)
def limit_clips(sender, instance, created, **kwargs):
    """
    Remove old clips when saving new clip if above MAX_CLIPS_PER_USER
    """
    num_clips = Clip.objects.filter(user=instance.user).count()
    if num_clips > settings.MAX_CLIPS_PER_USER:
        # Delete oldest clips
        last_pk_to_keep = (
            Clip.objects.filter(user=instance.user)
            .values("pk")[num_clips - settings.MAX_CLIPS_PER_USER]
            .get("pk")
        )
        Clip.objects.filter(user=instance.user, pk__lt=last_pk_to_keep).delete()
    else:
        pass
