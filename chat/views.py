from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from users.models import UserProfile
from .models import ChatRoom, Message, Notification
from .communication_matrix import (
    can_communicate,
    get_eligible_contacts,
    get_communication_rules,
    get_user_role
)


@login_required
def inbox(request):
    rooms = ChatRoom.objects.filter(participants=request.user, is_active=True)

    for room in rooms:
        room.unread_count = room.get_unread_count(request.user)
        room.last_message = room.messages.first()

    rules = get_communication_rules(request.user)
    eligible_contacts = get_eligible_contacts(request.user)

    context = {
        'rooms': rooms,
        'rules': rules,
        'user_role': get_user_role(request.user),
        'eligible_contacts': eligible_contacts,
    }
    return render(request, 'chat/inbox.html', context)


@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user, is_active=True)

    messages_to_read = room.messages.filter(is_read=False).exclude(sender=request.user)
    for msg in messages_to_read:
        msg.mark_as_read(request.user)

    eligible_contacts = get_eligible_contacts(request.user)
    other_participants = room.participants.exclude(id=request.user.id)

    context = {
        'room': room,
        'messages': room.messages.all()[:50],
        'eligible_contacts': eligible_contacts,
        'other_participants': other_participants,
        'user_role': get_user_role(request.user),
    }
    return render(request, 'chat/chat_room.html', context)


@login_required
def create_chat(request):
    if request.method == 'POST':
        participant_id = request.POST.get('participant_id')
        room_type = request.POST.get('room_type', 'direct')
        name = request.POST.get('name', '')

        participant = get_object_or_404(User, id=participant_id)

        if not can_communicate(request.user, participant):
            messages.error(request, 'You are not allowed to chat with this user.')
            return redirect('chat:inbox')

        if room_type == 'direct':
            existing_room = ChatRoom.objects.filter(
                room_type='direct',
                is_active=True
            ).filter(
                participants=request.user
            ).filter(
                participants=participant
            ).first()

            if existing_room:
                return redirect('chat:chat_room', room_id=existing_room.id)

        room = ChatRoom.objects.create(
            room_type=room_type,
            name=name or f"Chat with {participant.username}",
            created_by=request.user,
            is_active=True
        )
        room.participants.add(request.user, participant)

        Message.objects.create(
            room=room,
            sender=request.user,
            content=f"Chat started with {participant.username}",
            message_type='system'
        )

        return redirect('chat:chat_room', room_id=room.id)

    return redirect('chat:inbox')


@login_required
def send_message(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(ChatRoom, id=room_id, participants=request.user, is_active=True)
        content = request.POST.get('content', '').strip()

        if not content:
            return JsonResponse({'success': False, 'error': 'Message cannot be empty'})

        message = Message.objects.create(
            room=room,
            sender=request.user,
            content=content,
            message_type='text'
        )

        for participant in room.participants.exclude(id=request.user.id):
            Notification.objects.create(
                recipient=participant,
                sender=request.user,
                title=f'New message from {request.user.username}',
                message=content[:100],
                notification_type='message',
                link=f'/chat/room/{room.id}/'
            )

        return JsonResponse({
            'success': True,
            'message_id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'created_at': message.created_at.strftime('%Y-%m-%d %H:%M')
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required
def get_messages(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user, is_active=True)
    last_id = request.GET.get('last_id', 0)

    messages_list = room.messages.filter(id__gt=last_id)[:50]

    data = []
    for msg in messages_list:
        data.append({
            'id': msg.id,
            'sender': msg.sender.username,
            'content': msg.content,
            'message_type': msg.message_type,
            'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'),
            'is_read': msg.is_read,
        })

    return JsonResponse({'messages': data})


@login_required
def mark_read(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id, participants=request.user, is_active=True)

    messages_to_read = room.messages.filter(is_read=False).exclude(sender=request.user)
    for msg in messages_to_read:
        msg.mark_as_read(request.user)

    return JsonResponse({'success': True})


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    notifications.filter(is_read=False).update(is_read=True)

    context = {
        'notifications': notifications,
    }
    return render(request, 'chat/notifications.html', context)


@login_required
def notifications_api(request):
    notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')[:10]
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()

    data = []
    for notif in notifications:
        data.append({
            'id': notif.id,
            'title': notif.title,
            'message': notif.message,
            'link': notif.link or '#',
            'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M'),
        })

    return JsonResponse({
        'count': count,
        'notifications': data
    })


@login_required
def unread_count_api(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})