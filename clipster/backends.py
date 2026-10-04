from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.backends import ModelBackend
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from rest_framework.throttling import BaseThrottle


class LoginThrottleBackend(ModelBackend):
    """
    ModelBackend that limits failed logins per client. Every password check goes through it:
    web frontend and admin login as well as Basic Auth of the API clients.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if request is None:
            return super().authenticate(request, username, password, **kwargs)

        key = f"login_failures_{BaseThrottle().get_ident(request)}"
        if cache.get(key, 0) >= settings.LOGIN_FAILURE_LIMIT:
            # Lets the login forms tell the user why, see LoginThrottleMessageMixin
            request.login_throttled = True
            raise PermissionDenied

        user = super().authenticate(request, username, password, **kwargs)
        if user is None and not cache.add(key, 1, timeout=settings.LOGIN_FAILURE_WINDOW):
            try:
                cache.incr(key)
            except ValueError:  # expired in between
                cache.add(key, 1, timeout=settings.LOGIN_FAILURE_WINDOW)
        return user

    async def aauthenticate(self, request, username=None, password=None, **kwargs):
        return await sync_to_async(self.authenticate)(request, username, password, **kwargs)
