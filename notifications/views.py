from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404

from .models import Notification


@login_required
def notification_list(request):

    notifications = Notification.objects.filter(
        user=request.user
    ).order_by('-created_at')

    unread_count = notifications.filter(
        is_read=False
    ).count()

    notifications.filter(
        is_read=False
    ).update(
        is_read=True
    )

    return render(
        request,
        'notifications/notification_list.html',
        {
            'notifications': notifications,
            'unread_count': unread_count,
        }
    )


@login_required
def notification_summary(request):

    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')

    latest = [
        {
            'id': notification.id,
            'message': notification.message,
            'created_at': notification.created_at.strftime('%b %d, %Y %H:%M'),
        }
        for notification in unread_notifications[:5]
    ]

    return JsonResponse(
        {
            'success': True,
            'unread_count': unread_notifications.count(),
            'latest': latest,
        }
    )


@login_required
def mark_notifications_read(request):

    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(
        is_read=True
    )

    return redirect('notification_list')


@login_required
def delete_notification(request, notification_id):

    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )

    notification.delete()

    return redirect('notification_list')


@login_required
def clear_all_notifications(request):

    Notification.objects.filter(
        user=request.user
    ).delete()

    return redirect('notification_list')
