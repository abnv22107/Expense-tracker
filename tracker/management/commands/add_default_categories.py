from django.core.management.base import BaseCommand
from tracker.models import Category
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Adds default expense categories for all users'

    def handle(self, *args, **options):
        default_categories = [
            'Food',
            'Transportation',
            'Housing',
            'Utilities',
            'Entertainment',
            'Shopping',
            'Healthcare',
            'Education',
            'Personal Care',
            'Travel',
            'Gifts',
            'Other'
        ]

        users = User.objects.all()
        if not users.exists():
            self.stdout.write(self.style.WARNING('No users found in the system'))
            return

        total_created = 0
        for user in users:
            user_created = 0
            for category_name in default_categories:
                category, created = Category.objects.get_or_create(
                    name=category_name,
                    user=user
                )
                if created:
                    user_created += 1
                    total_created += 1
            
            if user_created > 0:
                self.stdout.write(self.style.SUCCESS(f'Added {user_created} categories for user {user.username}'))
            else:
                self.stdout.write(self.style.WARNING(f'All categories already exist for user {user.username}'))

        self.stdout.write(self.style.SUCCESS(f'Successfully added {total_created} new categories across all users')) 