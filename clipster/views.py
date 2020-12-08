from django.shortcuts import render, redirect
from django.http import Http404
from clipster.models import Clip
from clipster.serializers import ClipSerializer, UserSerializer
from clipster.permissions import IsOwnerOrReadOnly
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from rest_framework.renderers import TemplateHTMLRenderer


class ListClip(APIView):
    """
    List the clips if authenticated else redirect to login page
    """

    throttle_classes = (AnonRateThrottle, UserRateThrottle)
    renderer_classes = [TemplateHTMLRenderer]

    def get(self, request):
        if request.user.is_authenticated:
            clips = Clip.objects.filter(user=self.request.user)
            serializer = ClipSerializer(clips, many=True)
            return Response({"clips": clips}, template_name="rest_framework/list.html")
        return redirect("rest_framework:login")

    def post(self, request):
        permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)
        serializer = ClipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)  # explicitly specifying user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CopyPaste(APIView):
    """
    Update and retrieve the data.
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    throttle_classes = (AnonRateThrottle, UserRateThrottle)

    def get_clip(self, user):
        try:
            return Clip.objects.get(user=user)
        except Clip.DoesNotExist:
            raise Http404

    def post(self, request):
        clip = self.get_clip(request.user)
        serializer = ClipSerializer(clip, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        clip = self.get_clip(request.user)
        serializer = ClipSerializer(clip)
        return Response(serializer.data)


class UserRegister(APIView):
    """
    To register new users.
    """

    renderer_classes = [TemplateHTMLRenderer]
    throttle_classes = (AnonRateThrottle, UserRateThrottle)

    def get(self, request):
        form = UserCreationForm()
        return Response(
            data={"form": form}, template_name="rest_framework/register.html"
        )

    def post(self, request):
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect("list_clips")
        else:
            return Response(
                {"error": ["Error"], "form": form},
                status=status.HTTP_400_BAD_REQUEST,
                template_name="rest_framework/register.html",
            )


class UserVerify(APIView):
    """
    Check if user exists
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)

    def get(self, request):
        return Response(status=status.HTTP_200_OK)
