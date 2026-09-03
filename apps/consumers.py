import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.models import Conversation, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        if self.scope["user"].is_authenticated and await self.is_participant():
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()
        else:
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        text = data.get("text", "").strip()
        if not text:
            return

        message = await self.save_message(text)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": {
                    "id": str(message.id),
                    "sender_id": str(message.sender_id),
                    "text": message.text,
                    "created_at": message.created_at.isoformat(),
                },
            },
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))

    @database_sync_to_async
    def is_participant(self):
        try:
            conversation = Conversation.objects.get(pk=self.conversation_id)
            return self.scope["user"] in [conversation.buyer, conversation.seller]
        except Conversation.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, text):
        conversation = Conversation.objects.get(pk=self.conversation_id)
        return Message.objects.create(
            conversation=conversation,
            sender=self.scope["user"],
            text=text,
        )
