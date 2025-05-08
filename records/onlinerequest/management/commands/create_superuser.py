from django.core.management.base import BaseCommand
from onlinerequest.models import User

class Command(BaseCommand):
    help = 'Creates a default superuser'

    def handle(self, *args, **options):
        if not User.objects.filter(email='superuser').exists():
            user = User.objects.create(
                email='superuser',
                student_number='SUPER001',
                is_active=True,
                user_type=5  # Admin type from USER_TYPE_CHOICES
            )
            user.set_password('superuser')
            user.save()
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
