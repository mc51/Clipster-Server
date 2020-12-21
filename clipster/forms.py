from django.forms import ModelForm
from clipster.models import Clip


class ShareClipForm(ModelForm):
    class Meta:
        model = Clip
        fields = ["device", "user", "text"]
