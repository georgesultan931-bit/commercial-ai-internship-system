from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import Message, Notification


@login_required
def messages_view(request):
    messages_list = Message.objects.filter(recipient=request.user).order_by('-created_at')
    sent_messages = Message.objects.filter(sender=request.user).order_by('-created_at')
    unread_count = messages_list.filter(is_read=False).count()
    
    context = {
        'active_menu': 'messages',
        'messages': messages_list,
        'sent_messages': sent_messages,
        'unread_count': unread_count,
    }
    return render(request, 'communication/messages.html', context)


@login_required
def notifications(request):
    notifications_list = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifications_list.filter(is_read=False).count()
    
    context = {
        'active_menu': 'notifications',
        'notifications': notifications_list,
        'unread_count': unread_count,
    }
    return render(request, 'communication/notifications.html', context)


@login_required
def calendar(request):
    context = {
        'active_menu': 'calendar',
    }
    return render(request, 'communication/calendar.html', context)


@login_required
def inbox(request):
    messages_list = Message.objects.filter(recipient=request.user).order_by('-created_at')
    context = {
        'active_menu': 'messages',
        'messages': messages_list,
    }
    return render(request, 'communication/inbox.html', context)


@login_required
def sent_messages(request):
    messages_list = Message.objects.filter(sender=request.user).order_by('-created_at')
    context = {
        'active_menu': 'messages',
        'messages': messages_list,
    }
    return render(request, 'communication/sent.html', context)


@login_required
def chat(request, user_id):
    recipient = get_object_or_404(User, id=user_id)
    context = {
        'recipient': recipient,
        'active_menu': 'messages',
    }
    return render(request, 'communication/chat.html', context)