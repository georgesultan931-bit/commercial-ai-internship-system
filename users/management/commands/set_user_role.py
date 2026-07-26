from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from users.models import UserProfile

class Command(BaseCommand):
    help = 'Set role for a user'
    
    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username')
        parser.add_argument('role', type=str, help='Role: student, employer, supervisor, coordinator, admin')
    
    def handle(self, *args, **options):
        username = options['username']
        role = options['role']
        
        try:
            user = User.objects.get(username=username)
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.role = role
            profile.save()
            self.stdout.write(self.style.SUCCESS(f'Role for {username} set to {role}'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} not found'))