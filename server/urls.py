from django.contrib import admin
from django.urls import include, re_path

from clipster import views as cb

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(r"^$|^accounts/profile/", cb.ListClip.as_view(), name="list_clips_frontend"),
    re_path(r"^share-clip/", cb.ShareClip.as_view(), name="share_clip"),
    re_path(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    re_path(r"^copy-paste/", cb.CopyPaste.as_view(), name="copy_paste"),
    re_path(r"^register/", cb.UserRegister.as_view(), name="register"),
    re_path(r"^verify-user/", cb.UserVerify.as_view(), name="verify"),
]
