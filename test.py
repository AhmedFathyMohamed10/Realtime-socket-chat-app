import asyncio
import websockets
import json

# Change these before running:
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU4MDQ5Njc1LCJpYXQiOjE3NTgwMzQ2NzUsImp0aSI6ImFiYmE0MzUzZmU0MTQ4MzQ5Y2YyYWRkZmRlNGQ0MDU0IiwidXNlcl9pZCI6MX0.An9A-gm04ALODiJvM7gfcNGjGRxFB8ubG3LXM5OVffE"
ROOM_ID = "d4fe893b-c94b-482d-b9e1-99298a53acb4"  # must match a ChatRoom in your DB
BASE_URL = "ws://localhost:8001"
USER_ID=1


async def test_echo():
    uri = f"{BASE_URL}/ws/echo/"
    async with websockets.connect(uri) as ws:
        print("✅ Connected to EchoConsumer")

        await ws.send("Hello Echo!")
        response = await ws.recv()
        print("Echo Response:", response)


async def test_chat():
    uri = f"{BASE_URL}/ws/chat/{ROOM_ID}/?token={JWT_TOKEN}"
    async with websockets.connect(uri) as ws:
        print("✅ Connected to ChatConsumer")

        # Send a chat message
        message = {
            "type": "chat_message",
            "message": "Hello from test client 🚀"
        }
        await ws.send(json.dumps(message))

        # Wait for server response
        response = await ws.recv()
        print("Chat Response:", response)

        # Send typing indicator
        typing = {"type": "typing", "is_typing": True}
        await ws.send(json.dumps(typing))

        # Wait for typing broadcast (if any)
        try:
            response = await asyncio.wait_for(ws.recv(), timeout=2)
            print("Typing Event:", response)
        except asyncio.TimeoutError:
            print("⏳ No typing event received (expected if no other users).")


async def test_notifications():
    uri = f"{BASE_URL}/ws/notifications/{USER_ID}/"
    async with websockets.connect(uri) as ws:
        print("✅ Connected to NotificationConsumer")

        print("ℹ️ Now open a Django shell and run:")
        print(f"""
from channels.layers import get_channel_layer
import asyncio

channel_layer = get_channel_layer()
async def send_notification():
    await channel_layer.group_send(
        "notifications_{USER_ID}",
        {{"type": "notification_message", "notification": "🔔 Test notification"}}
    )

asyncio.run(send_notification())
        """)

        # Wait for notification
        response = await ws.recv()
        print("Notification Received:", response)


async def main():
    print("\n--- Testing EchoConsumer ---")
    await test_echo()

    print("\n--- Testing ChatConsumer ---")
    await test_chat()

    print("\n--- Testing NotificationConsumer ---")
    await test_notifications()


if __name__ == "__main__":
    asyncio.run(main())
