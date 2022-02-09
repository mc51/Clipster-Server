"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import re_path, include, path
from django.shortcuts import redirect
from django.contrib import admin
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
