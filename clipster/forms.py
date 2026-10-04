from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from clipster.models import Clip


class ShareClipForm(ModelForm):
    class Meta:
        model = Clip
        fields = ["device", "format", "text"]


class LoginThrottleMessageMixin:
    """
    Show why a login was refused when LoginThrottleBackend blocked it
    """

    def get_invalid_login_error(self):
        if getattr(self.request, "login_throttled", False):
            return ValidationError(
                "Too many failed login attempts. Please wait a minute and try again.",
                code="throttled",
            )
        return super().get_invalid_login_error()


class LoginForm(LoginThrottleMessageMixin, AuthenticationForm):
    pass


class AdminLoginForm(LoginThrottleMessageMixin, AdminAuthenticationForm):
    pass
