def sidebar_context(request):
    """
    Context processor to add sidebar data to all templates.
    """
    from django.contrib.auth.models import User
    from django.db.models import Count
    
    context = {
        'total_users': User.objects.count(),
        'total_internships': 0,
        'total_applications': 0,
    }
    
    try:
        from internships.models import Internship
        context['total_internships'] = Internship.objects.filter(is_active=True).count()
    except:
        pass
    
    try:
        from applications.models import Application
        context['total_applications'] = Application.objects.count()
    except:
        pass
    
    if request.user.is_authenticated:
        try:
            from communication.models import Message
            context['messages_count'] = Message.objects.filter(receiver=request.user, is_read=False).count()
        except:
            context['messages_count'] = 0
        
        try:
            from communication.models import Notification
            context['notifications_count'] = Notification.objects.filter(user=request.user, is_read=False).count()
        except:
            context['notifications_count'] = 0
    
    return context


def notification_counts(request):
    """
    Context processor to add notification counts to all templates.
    """
    if request.user.is_authenticated:
        try:
            from communication.models import Message, Notification
            return {
                'unread_messages_count': Message.objects.filter(receiver=request.user, is_read=False).count(),
                'unread_notifications_count': Notification.objects.filter(user=request.user, is_read=False).count(),
            }
        except:
            return {
                'unread_messages_count': 0,
                'unread_notifications_count': 0,
            }
    return {
        'unread_messages_count': 0,
        'unread_notifications_count': 0,
    }