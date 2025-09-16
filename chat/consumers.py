import json
import traceback
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model



class EchoConsumer(AsyncWebsocketConsumer):
    """Simple echo test consumer for debugging WebSocket connections."""

    async def connect(self):
        await self.accept()
        await self.send(json.dumps({"msg": "✅ Connected to EchoConsumer"}))

    async def receive(self, text_data=None, bytes_data=None):
        await self.send(json.dumps({"echo": text_data}))


class ChatConsumer(AsyncWebsocketConsumer):
    """Main chat consumer for handling rooms, messages, typing, and status."""

    async def connect(self):
        try:
            self.room_id = self.scope["url_route"]["kwargs"].get("room_id")
            if not self.room_id:
                await self.close(code=4000)  # invalid room id
                return

            self.room_group_name = f"chat_{self.room_id}"

            # Enforce authentication (JWTAuthMiddleware sets scope["user"])
            user = self.scope.get("user")
            if not user or not user.is_authenticated:
                await self.close(code=4001)  # unauthorized
                return

            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
            print(f"✅ Connection accepted for user {user}")
        except Exception as e:
            print("❌ Error during connect:", e)
            traceback.print_exc()
            await self.close(code=1011)

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        except Exception:
            pass

        user = self.scope.get("user")
        if user and user.is_authenticated:
            await self.update_user_online_status(False)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        message_type = data.get("type", "chat_message")

        if message_type == "chat_message":
            await self.handle_chat_message(data)
        elif message_type == "message_status":
            await self.handle_message_status(data)
        elif message_type == "typing":
            await self.handle_typing(data)

    # --- Handlers ---

    async def handle_chat_message(self, data):
        content = data.get("message")
        if not content:
            return

        reply_to_id = data.get("reply_to")
        message = await self.save_message(self.scope["user"], self.room_id, content, reply_to_id)

        if not message:
            return

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": {
                    "id": str(message.id),
                    "content": message.content,
                    "sender": {
                        "id": message.sender.id,
                        "username": message.sender.username,
                        "profile_image": getattr(
                            getattr(message.sender, "profile_image", None), "url", None
                        ),
                    },
                    "created_at": message.created_at.isoformat(),
                },
            },
        )

    async def handle_message_status(self, data):
        message_id = data.get("message_id")
        status = data.get("status")
        if message_id and status:
            await self.update_message_status(message_id, status)

    async def handle_typing(self, data):
        is_typing = data.get("is_typing", False)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "typing_indicator",
                "user_id": self.scope["user"].id,
                "username": self.scope["user"].username,
                "is_typing": is_typing,
            },
        )

    # --- Group event handlers ---

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"type": "chat_message", "message": event["message"]}))

    async def typing_indicator(self, event):
        if event["user_id"] != self.scope["user"].id:
            await self.send(
                text_data=json.dumps(
                    {
                        "type": "typing",
                        "user_id": event["user_id"],
                        "username": event["username"],
                        "is_typing": event["is_typing"],
                    }
                )
            )

    # --- Database helpers ---

    @database_sync_to_async
    def save_message(self, user, room_id, content, reply_to_id=None):
        from .models import ChatRoom, Message

        if not user or not user.is_authenticated:
            return None

        try:
            room = ChatRoom.objects.get(id=room_id)
        except ChatRoom.DoesNotExist:
            return None

        reply_to = None
        if reply_to_id:
            try:
                reply_to = Message.objects.get(id=reply_to_id)
            except Message.DoesNotExist:
                reply_to = None

        return Message.objects.create(room=room, sender=user, content=content, reply_to=reply_to)

    @database_sync_to_async
    def update_message_status(self, message_id, status):
        from .models import Message, MessageStatus

        try:
            message = Message.objects.get(id=message_id)
            msg_status, created = MessageStatus.objects.get_or_create(
                message=message, user=self.scope["user"], defaults={"status": status}
            )
            if not created:
                msg_status.status = status
                msg_status.save()
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def update_user_online_status(self, is_online: bool):
        User = get_user_model()
        try:
            user = User.objects.get(id=self.scope["user"].id)
            user.is_online = is_online
            user.save()
        except User.DoesNotExist:
            pass


class NotificationConsumer(AsyncWebsocketConsumer):
    """Consumer for sending per-user notification updates."""

    async def connect(self):
        try:
            self.user_id = self.scope["url_route"]["kwargs"].get("user_id")
            if not self.user_id:
                await self.close(code=4000)
                return

            self.notification_group_name = f"notifications_{self.user_id}"
            await self.channel_layer.group_add(self.notification_group_name, self.channel_name)
            await self.accept()
        except Exception as e:
            print("❌ Error in NotificationConsumer.connect:", e)
            traceback.print_exc()
            await self.close(code=1011)

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(self.notification_group_name, self.channel_name)
        except Exception:
            pass

    async def notification_message(self, event):
        await self.send(
            text_data=json.dumps({"type": "notification", "notification": event.get("notification")})
        )
