from django.urls import re_path
from chat.consumers import ChatConsumer, NotificationConsumer, EchoConsumer

websocket_urlpatterns = [
    re_path(r"ws/echo/$", EchoConsumer.as_asgi()),
    re_path(r"ws/chat/(?P<room_id>[^/]+)/$", ChatConsumer.as_asgi()),
    re_path(r"ws/notifications/(?P<user_id>[^/]+)/$", NotificationConsumer.as_asgi()),
]
