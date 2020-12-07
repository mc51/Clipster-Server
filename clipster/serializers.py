from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from clipster.models import Clip
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User


class ClipSerializer(serializers.ModelSerializer):
    # Using ModelSerializers is just shortcut for Serializers
    # with default create and update
    user = serializers.ReadOnlyField(source="user.username")

    class Meta:
        model = Clip
        fields = ("id", "user", "text", "device")


class UserSerializer(serializers.ModelSerializer):
    # User object: username and hashed password
    def create(self, valid_data):
        user = User(username=valid_data["username"])
        user.set_password(valid_data["password"])
        user.save()
        return user

    class Meta:
        model = User
        # extra_kwargs = {'password': {'write_only': True}}
        fields = ("id", "username", "password")


@receiver(post_save, sender=User)
def init_clip(sender, instance, created, **kwargs):
    """
    Create a dummy clip for new user.
    """
    if created:
        clip = Clip.objects.create(
            text="Hi %s! Your clip goes here." % instance.username, user=instance
        )
    else:
        pass
