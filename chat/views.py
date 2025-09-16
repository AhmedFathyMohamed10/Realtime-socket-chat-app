from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Max
from .models import ChatRoom, Message, ChatRoomMembership, MessageStatus
from .serializers import ( # type: ignore
    ChatRoomSerializer, MessageSerializer, CreatePrivateChatSerializer,
    CreateGroupChatSerializer, SendMessageSerializer
)
from notifications.models import Notification # type: ignore
from channels.layers import get_channel_layer
import json

User = get_user_model()
channel_layer = get_channel_layer()

class ChatRoomListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        return ChatRoom.objects.filter(
            members=self.request.user
        ).annotate(
            last_message_time=Max('messages__created_at')
        ).order_by('-last_message_time')


class CreatePrivateChatView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreatePrivateChatSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        other_user_id = serializer.validated_data['user_id']
        other_user = User.objects.get(id=other_user_id)
        
        # Check if private chat already exists
        existing_room = ChatRoom.objects.filter(
            room_type='private',
            members=request.user
        ).filter(
            members=other_user
        ).first()
        
        if existing_room:
            return Response(
                ChatRoomSerializer(existing_room, context={'request': request}).data,
                status=status.HTTP_200_OK
            )
        
        # Create new private chat
        room = ChatRoom.objects.create(
            room_type='private',
            created_by=request.user
        )
        
        # Add members
        ChatRoomMembership.objects.create(user=request.user, room=room, role='admin')
        ChatRoomMembership.objects.create(user=other_user, room=room, role='member')
        
        # Create notification
        Notification.objects.create(
            user=other_user,
            title="New Chat",
            message=f"{request.user.full_name} started a chat with you",
            notification_type='chat',
            related_object_id=str(room.id)
        )
        
        return Response(
            ChatRoomSerializer(room, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class CreateGroupChatView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CreateGroupChatSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        name = serializer.validated_data['name']
        description = serializer.validated_data.get('description', '')
        user_ids = serializer.validated_data['user_ids']
        
        # Create group chat
        room = ChatRoom.objects.create(
            name=name,
            description=description,
            room_type='group',
            created_by=request.user
        )
        
        # Add creator as admin
        ChatRoomMembership.objects.create(
            user=request.user, 
            room=room, 
            role='admin'
        )
        
        # Add other members
        users = User.objects.filter(id__in=user_ids)
        for user in users:
            ChatRoomMembership.objects.create(
                user=user, 
                room=room, 
                role='member'
            )
            
            # Create notification
            Notification.objects.create(
                user=user,
                title="Added to Group",
                message=f"{request.user.full_name} added you to {name}",
                notification_type='chat',
                related_object_id=str(room.id)
            )
        
        return Response(
            ChatRoomSerializer(room, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


class ChatRoomDetailView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChatRoomSerializer

    def get_queryset(self):
        return ChatRoom.objects.filter(members=self.request.user)


class MessageListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        room_id = self.kwargs['room_id']
        
        # Verify user is member of the room
        try:
            room = ChatRoom.objects.get(id=room_id, members=self.request.user)
            return room.messages.all().order_by('-created_at')
        except ChatRoom.DoesNotExist:
            return Message.objects.none()


class SendMessageView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SendMessageSerializer

    def create(self, request, *args, **kwargs):
        room_id = self.kwargs['room_id']
        
        try:
            room = ChatRoom.objects.get(id=room_id, members=request.user)
        except ChatRoom.DoesNotExist:
            return Response(
                {'error': 'Room not found or access denied'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create message
        message = Message.objects.create(
            room=room,
            sender=request.user,
            **serializer.validated_data
        )
        
        # Create message status for all members except sender
        for membership in room.memberships.exclude(user=request.user):
            MessageStatus.objects.create(
                message=message,
                user=membership.user,
                status='delivered'
            )
        
        # Create notifications for all members except sender
        for membership in room.memberships.exclude(user=request.user):
            if not membership.is_muted:
                Notification.objects.create(
                    user=membership.user,
                    title=f"New message from {request.user.full_name}",
                    message=message.content[:100],
                    notification_type='message',
                    related_object_id=str(room.id)
                )
        
        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_message_as_read(request, message_id):
    """Mark a specific message as read"""
    try:
        message = Message.objects.get(id=message_id)
        
        # Check if user is member of the room
        if not message.room.members.filter(id=request.user.id).exists():
            return Response(
                {'error': 'Access denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Update message status
        message_status, created = MessageStatus.objects.get_or_create(
            message=message,
            user=request.user,
            defaults={'status': 'read'}
        )
        
        if not created and message_status.status != 'read':
            message_status.status = 'read'
            message_status.save()
        
        return Response({'status': 'success'})
        
    except Message.DoesNotExist:
        return Response(
            {'error': 'Message not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_all_messages_read(request, room_id):
    """Mark all messages in a room as read"""
    try:
        room = ChatRoom.objects.get(id=room_id, members=request.user)
        
        # Get all unread messages for this user in this room
        unread_messages = Message.objects.filter(
            room=room
        ).exclude(
            statuses__user=request.user,
            statuses__status='read'
        )
        
        # Mark all as read
        for message in unread_messages:
            message_status, created = MessageStatus.objects.get_or_create(
                message=message,
                user=request.user,
                defaults={'status': 'read'}
            )
            if not created:
                message_status.status = 'read'
                message_status.save()
        
        return Response({'status': 'success'})
        
    except ChatRoom.DoesNotExist:
        return Response(
            {'error': 'Room not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def leave_room(request, room_id):
    """Leave a chat room"""
    try:
        room = ChatRoom.objects.get(id=room_id)
        membership = ChatRoomMembership.objects.get(room=room, user=request.user)
        
        if room.room_type == 'private':
            return Response(
                {'error': 'Cannot leave private chat'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If user is admin and there are other members, transfer admin to another member
        if membership.role == 'admin':
            other_members = ChatRoomMembership.objects.filter(
                room=room
            ).exclude(user=request.user)
            
            if other_members.exists():
                # Transfer admin to first member
                other_members.first().role = 'admin'
                other_members.first().save()
        
        # Remove membership
        membership.delete()
        
        # Create notification for remaining members
        for remaining_membership in room.chatroommembership_set.all():
            Notification.objects.create(
                user=remaining_membership.user,
                title="Member Left",
                message=f"{request.user.full_name} left the group",
                notification_type='chat',
                related_object_id=str(room.id)
            )
        
        return Response({'status': 'success'})
        
    except (ChatRoom.DoesNotExist, ChatRoomMembership.DoesNotExist):
        return Response(
            {'error': 'Room or membership not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def add_member_to_group(request, room_id):
    """Add a member to a group chat"""
    try:
        room = ChatRoom.objects.get(id=room_id, room_type='group')
        membership = ChatRoomMembership.objects.get(room=room, user=request.user)
        
        # Only admins can add members
        if membership.role != 'admin':
            return Response(
                {'error': 'Only admins can add members'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        user_id = request.data.get('user_id')
        try:
            new_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if user is already a member
        if ChatRoomMembership.objects.filter(room=room, user=new_user).exists():
            return Response(
                {'error': 'User is already a member'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add member
        ChatRoomMembership.objects.create(
            user=new_user,
            room=room,
            role='member'
        )
        
        # Create notification for new member
        Notification.objects.create(
            user=new_user,
            title="Added to Group",
            message=f"{request.user.full_name} added you to {room.name}",
            notification_type='chat',
            related_object_id=str(room.id)
        )
        
        # Create notification for other members
        for other_membership in room.chatroomMembership_set.exclude(
            user__in=[request.user, new_user]
        ):
            Notification.objects.create(
                user=other_membership.user,
                title="New Member",
                message=f"{request.user.full_name} added {new_user.full_name}",
                notification_type='chat',
                related_object_id=str(room.id)
            )
        
        return Response({'status': 'success'})
        
    except (ChatRoom.DoesNotExist, ChatRoomMembership.DoesNotExist):
        return Response(
            {'error': 'Room or membership not found'},
            status=status.HTTP_404_NOT_FOUND
        )