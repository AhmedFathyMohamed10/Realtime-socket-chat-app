from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from .serializers import ( # type: ignore
    UserRegistrationSerializer, 
    UserSerializer, 
    UserUpdateSerializer,
    UserProfileSerializer
)
from notifications.models import Notification # type: ignore

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201:
            # Create registration notification
            user = User.objects.get(email=request.data['email'])
            Notification.objects.create(
                user=user,
                title="Account Created",
                message="Your account has been successfully created!",
                notification_type='account'
            )
        return response


class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UpdateProfileView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserUpdateSerializer

    def get_object(self):
        return self.request.user


class UserListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer
    
    def get_queryset(self):
        return User.objects.exclude(id=self.request.user.id)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_online_status(request):
    """Update user online status"""
    is_online = request.data.get('is_online', False)
    request.user.is_online = is_online
    request.user.save()
    
    return Response({
        'status': 'success',
        'is_online': is_online
    })