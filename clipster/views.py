from django.shortcuts import redirect
from django.http import Http404
from clipster.models import Clip
from clipster.forms import ShareClipForm
from clipster.serializers import ClipSerializer, UserSerializer
from clipster.permissions import IsOwnerOrReadOnly
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.password_validation import validate_password, ValidationError


class ListClip(APIView):
    """
    List the clips if authenticated else redirect to login page
    """

    throttle_classes = (AnonRateThrottle, UserRateThrottle)
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]

    def get(self, request):
        if request.user.is_authenticated:
            clips = Clip.objects.filter(user=request.user)
            serializer = ClipSerializer(clips, many=True)
            if serializer:  # ignore pylint warning
                pass
            return Response({"clips": clips}, template_name="rest_framework/list.html")
        return redirect("rest_framework:login")

    def post(self, request):
        permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)
        if permission_classes:  # ignore pylint warning
            pass
        serializer = ClipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)  # explicitly specifying user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CopyPaste(APIView):
    """
    Create new Clip or return last Clip
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
    throttle_classes = (AnonRateThrottle, UserRateThrottle)

    def get_last_clip(self, user):
        # Get last clip
        try:
            return Clip.objects.filter(user=user).last()
        except Clip.DoesNotExist:
            raise Http404

    def post(self, request):
        # Create new Clip and save
        serializer = ClipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        clip = self.get_last_clip(request.user)
        serializer = ClipSerializer(clip)
        return Response(serializer.data)


class UserRegister(APIView):
    """
    Register new user
    Respond to html and json requests differently
    """

    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    throttle_classes = (AnonRateThrottle, UserRateThrottle)

    def get(self, request):
        form = UserCreationForm()
        return Response(
            data={"form": form}, template_name="rest_framework/register.html"
        )

    def post(self, request):
        # Handle html and json response differently
        if request.accepted_renderer.format == "html":
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
        elif request.accepted_renderer.format == "json":
            try:
                validate_password(request.data["password"])
            except ValidationError as e:
                return Response(e, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer = UserSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    return Response(
                        serializer.data["username"], status=status.HTTP_201_CREATED
                    )
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserVerify(APIView):
    """
    Check if user exists
    """

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)

    def get(self, request):
        return Response(status=status.HTTP_200_OK)


class ShareClip(APIView):
    """
    Let user share Clip if authenticated
    """

    renderer_classes = [TemplateHTMLRenderer]
    throttle_classes = (AnonRateThrottle, UserRateThrottle)

    def get(self, request):
        if request.user.is_authenticated:
            form = ShareClipForm()
            return Response(
                data={"form": form}, template_name="rest_framework/share_clip.html"
            )
        return redirect("rest_framework:login")

    def post(self, request):
        form = ShareClipForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("list_clips")
        else:
            return Response(
                {"error": ["Error"], "form": form},
                status=status.HTTP_400_BAD_REQUEST,
                template_name="rest_framework/share_clip.html",
            )
