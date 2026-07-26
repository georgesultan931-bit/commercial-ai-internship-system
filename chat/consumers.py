import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check if user is in this chat room
        if not await self.is_user_in_room(self.room_id, self.user):
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Set user as online
        await self.set_user_online(self.user, True)
        
        # Send online status to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'is_online': True
            }
        )
    
    async def disconnect(self, close_code):
        # Set user as offline
        await self.set_user_online(self.user, False)
        
        # Send offline status to room
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'is_online': False
            }
        )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            content = data.get('content', '').strip()
            if content:
                # Save message to database
                message = await self.save_message(self.room_id, self.user, content)
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message_id': message.id,
                        'sender_id': self.user.id,
                        'sender_name': self.user.first_name or self.user.username,
                        'content': content,
                        'created_at': timezone.now().isoformat(),
                        'is_read': False
                    }
                )
        
        elif message_type == 'typing':
            # Send typing indicator
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'is_typing': data.get('is_typing', False)
                }
            )
        
        elif message_type == 'mark_read':
            # Mark messages as read
            await self.mark_messages_read(self.room_id, self.user)
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'messages_read',
                    'user_id': self.user.id
                }
            )
    
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'content': event['content'],
            'created_at': event['created_at'],
            'is_read': event['is_read']
        }))
    
    async def user_status(self, event):
        # Send user status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'status',
            'user_id': event['user_id'],
            'is_online': event['is_online']
        }))
    
    async def typing_indicator(self, event):
        # Send typing indicator to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        }))
    
    async def messages_read(self, event):
        # Send read receipt to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'user_id': event['user_id']
        }))
    
    @database_sync_to_async
    def is_user_in_room(self, room_id, user):
        try:
            from chat.models import ChatRoom
            return ChatRoom.objects.filter(id=room_id, participants=user).exists()
        except:
            return False
    
    @database_sync_to_async
    def save_message(self, room_id, user, content):
        from chat.models import ChatRoom, Message
        room = ChatRoom.objects.get(id=room_id)
        return Message.objects.create(room=room, sender=user, content=content)
    
    @database_sync_to_async
    def set_user_online(self, user, is_online):
        try:
            from chat.models import UserStatus
            status, created = UserStatus.objects.get_or_create(user=user)
            status.is_online = is_online
            if not is_online:
                status.last_seen = timezone.now()
            status.save()
        except:
            pass
    
    @database_sync_to_async
    def mark_messages_read(self, room_id, user):
        try:
            from chat.models import ChatRoom, Message
            room = ChatRoom.objects.get(id=room_id)
            Message.objects.filter(room=room).exclude(sender=user).update(
                is_read=True,
                read_at=timezone.now()
            )
        except:
            pass