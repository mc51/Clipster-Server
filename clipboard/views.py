from django.shortcuts import render
from django.http import Http404
from clipboard.models import Clip
from clipboard.serializers import ClipSerializer, UserSerializer
from clipboard.permissions import IsOwnerOrReadOnly
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import permissions
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth.password_validation import validate_password, ValidationError

# ToDos: Rate Limits per user and total for login  / register

class ListClip(APIView):
    """
    List the most recently copied texts. I am calling them 'clips'.
    """
    def get(self, request):
        # Only show own clips
        clips = Clip.objects.filter(user=self.request.user)
        serializer = ClipSerializer(clips, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = ClipSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=self.request.user)  # explicitly specifying user
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    permission_classes = (permissions.IsAuthenticated, IsOwnerOrReadOnly)


class CopyPaste(APIView):
    """
    Update and retrieve the data.
    """
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

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)


class UserRegister(APIView):
    """
    To register new users.
    """

    throttle_classes = (AnonRateThrottle,)

    def post(self, request):
        try:
            validate_password(request.data['password'])
        except ValidationError as e:
            return Response(e, status=status.HTTP_400_BAD_REQUEST)
        else:
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data['username'], status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserVerify(APIView):

    def get(self, request):
        return Response(status=status.HTTP_200_OK)

    permission_classes = (permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly)
