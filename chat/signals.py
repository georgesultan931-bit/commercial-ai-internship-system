from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Notification
from users.models import UserProfile


@receiver(post_save, sender=User)
def notify_admin_on_new_user(sender, instance, created, **kwargs):
    """Notify admin when a new user registers"""
    if created:
        try:
            # Get the user profile to check role
            profile = UserProfile.objects.get(user=instance)
            role = profile.role
        except UserProfile.DoesNotExist:
            role = 'Unknown'
        
        admin_users = User.objects.filter(is_superuser=True)
        for admin in admin_users:
            Notification.objects.create(
                recipient=admin,
                sender=instance,
                title=f'New User Registration',
                message=f'User {instance.username} has registered as {role}',
                notification_type='system',
                link='/admin-dashboard/'
            )


@receiver(post_save, sender=UserProfile)
def notify_admin_on_profile_update(sender, instance, created, **kwargs):
    """Notify admin when a user profile is updated or created"""
    if created:
        # Skip if user was already handled by user signal
        pass
    else:
        # Notify admin if role changed
        admin_users = User.objects.filter(is_superuser=True)
        for admin in admin_users:
            Notification.objects.create(
                recipient=admin,
                sender=instance.user,
                title=f'Profile Updated',
                message=f'User {instance.user.username} updated their profile',
                notification_type='system',
                link='/admin-dashboard/'
            )