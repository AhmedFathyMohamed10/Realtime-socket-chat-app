from django.db import models
from django.conf import settings
import uuid

User = settings.AUTH_USER_MODEL


class ChatRoom(models.Model):
    ROOM_TYPES = [
        ('private', 'Private'),
        ('group', 'Group'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, blank=True)
    room_type = models.CharField(max_length=10, choices=ROOM_TYPES, default='private')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='room_images/', null=True, blank=True)

    members = models.ManyToManyField(
        User,
        through='ChatRoomMembership',
        related_name='chat_rooms'
    )

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_rooms'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.name or f"{self.room_type} Chat"


class ChatRoomMembership(models.Model):
    ROLES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    role = models.CharField(max_length=10, choices=ROLES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_muted = models.BooleanField(default=False)

    class Meta:
        unique_together = ['user', 'room']

    def __str__(self):
        return f"{self.user} in {self.room}"


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('audio', 'Audio'),
        ('video', 'Video'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')

    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')

    content = models.TextField(blank=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    file = models.FileField(upload_to='message_files/', null=True, blank=True)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender}: {self.content[:30]}"


class MessageStatus(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]

    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='statuses')

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['message', 'user']

    def __str__(self):
        return f"{self.user} -> {self.status}"