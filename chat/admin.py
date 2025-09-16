from django.contrib import admin
from .models import ChatRoom, Message, ChatRoomMembership, MessageStatus

class ChatRoomMembershipInline(admin.TabularInline):
    model = ChatRoomMembership
    extra = 0

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'created_by', 'created_at')
    list_filter = ('room_type', 'created_at')
    search_fields = ('name', 'created_by__username')
    inlines = [ChatRoomMembershipInline]

class MessageStatusInline(admin.TabularInline):
    model = MessageStatus
    extra = 0

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'room', 'content_preview', 'message_type', 'created_at')
    list_filter = ('message_type', 'created_at', 'is_edited')
    search_fields = ('content', 'sender__username', 'room__name')
    inlines = [MessageStatusInline]
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(ChatRoomMembership)
class ChatRoomMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'role', 'joined_at', 'is_muted')
    list_filter = ('role', 'is_muted', 'joined_at')
    search_fields = ('user__username', 'room__name')

@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'status', 'timestamp')
    list_filter = ('status', 'timestamp')
    search_fields = ('message__content', 'user__username')