from django.urls import path
from chat.consumers import ChatConsumer, EchoConsumer, NotificationConsumer

websocket_urlpatterns = [
    path("ws/echo/", EchoConsumer.as_asgi()),
    path("ws/chat/<uuid:room_id>/", ChatConsumer.as_asgi()),
    path("ws/notifications/<int:user_id>/", NotificationConsumer.as_asgi()),
]