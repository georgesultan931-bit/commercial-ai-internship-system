from django import template

from internships.models import ApplicationMessage


register = template.Library()


@register.simple_tag
def unread_chat_count(user):

    if not getattr(user, 'is_authenticated', False):
        return 0

    if user.is_staff or user.is_superuser:
        return ApplicationMessage.objects.exclude(
            sender=user
        ).filter(
            is_read=False
        ).count()

    role = getattr(user, 'role', None)

    if role == 'student':

        return ApplicationMessage.objects.filter(
            application__student__user=user,
            is_read=False,
            deleted_for_student=False
        ).exclude(
            sender=user
        ).count()

    if role == 'employer':

        return ApplicationMessage.objects.filter(
            application__opportunity__employer__user=user,
            is_read=False,
            deleted_for_employer=False
        ).exclude(
            sender=user
        ).count()

    return 0