from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, ChatRoomMembership, MessageStatus
from accounts.serializers import UserSerializer # type: ignore

User = get_user_model()

class ChatRoomMembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ChatRoomMembership
        fields = ['user', 'role', 'joined_at', 'is_muted']


class MessageStatusSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = MessageStatus
        fields = ['user', 'status', 'timestamp']


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    reply_to = serializers.SerializerMethodField()
    statuses = MessageStatusSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'id', 'content', 'message_type', 'file', 'sender', 
            'reply_to', 'is_edited', 'edited_at', 'created_at', 'statuses'
        ]

    def get_reply_to(self, obj):
        if obj.reply_to:
            return {
                'id': obj.reply_to.id,
                'content': obj.reply_to.content,
                'sender': obj.reply_to.sender.username,
                'created_at': obj.reply_to.created_at
            }
        return None


class ChatRoomSerializer(serializers.ModelSerializer):
    members = ChatRoomMembershipSerializer(source='chatroomMembership_set', many=True, read_only=True)
    last_message = MessageSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'room_type', 'description', 'image',
            'members', 'last_message', 'created_at', 'updated_at', 'unread_count'
        ]

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Count messages that are not read by the current user
            return obj.messages.exclude(
                statuses__user=request.user,
                statuses__status='read'
            ).count()
        return 0


class CreatePrivateChatSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()

    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        return value


class CreateGroupChatSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(required=False, allow_blank=True)
    user_ids = serializers.ListField(child=serializers.IntegerField())

    def validate_user_ids(self, value):
        if len(value) < 1:
            raise serializers.ValidationError("At least one user is required.")
        
        users = User.objects.filter(id__in=value)
        if len(users) != len(value):
            raise serializers.ValidationError("Some users not found.")
        
        return value


class SendMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['content', 'message_type', 'file', 'reply_to']