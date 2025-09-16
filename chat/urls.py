from django.urls import path
from . import views

urlpatterns = [
    path('rooms/', views.ChatRoomListView.as_view(), name='chat_room_list'),
    path('rooms/<uuid:pk>/', views.ChatRoomDetailView.as_view(), name='chat_room_detail'),
    path('rooms/<uuid:room_id>/messages/', views.MessageListView.as_view(), name='message_list'),
    path('rooms/<uuid:room_id>/send/', views.SendMessageView.as_view(), name='send_message'),
    path('rooms/<uuid:room_id>/read-all/', views.mark_all_messages_read, name='mark_all_read'),
    path('rooms/<uuid:room_id>/leave/', views.leave_room, name='leave_room'),
    path('rooms/<uuid:room_id>/add-member/', views.add_member_to_group, name='add_member'),
    
    path('create/private/', views.CreatePrivateChatView.as_view(), name='create_private_chat'),
    path('create/group/', views.CreateGroupChatView.as_view(), name='create_group_chat'),
    
    path('messages/<uuid:message_id>/read/', views.mark_message_as_read, name='mark_message_read'),
]