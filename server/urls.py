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
from django.conf.urls import url, include
from django.shortcuts import redirect
from django.contrib import admin
from clipster import views as cb

urlpatterns = [
    url(r"^admin/", admin.site.urls),
    url(r"^$|^accounts/profile/", cb.ListClip.as_view(), name="list_clips_frontend"),
    url(r"^share-clip/", cb.ShareClip.as_view(), name="share_clip"),
    url(r"^api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    url(r"^copy-paste/", cb.CopyPaste.as_view(), name="copy_paste"),
    url(r"^register/", cb.UserRegister.as_view(), name="register"),
    url(r"^verify-user/", cb.UserVerify.as_view(), name="verify"),
]
