from django.db import migrations

def add_savings_categories(apps, schema_editor):
    Category = apps.get_model('tracker', 'Category')
    User = apps.get_model('auth', 'User')
    
    # Get all users
    users = User.objects.all()
    
    # Add savings categories for each user
    for user in users:
        # Create Savings category
        Category.objects.get_or_create(
            name='Savings',
            user=user
        )
        
        # Create Mutual Funds category
        Category.objects.get_or_create(
            name='Mutual Funds',
            user=user
        )

def remove_savings_categories(apps, schema_editor):
    Category = apps.get_model('tracker', 'Category')
    Category.objects.filter(name__in=['Savings', 'Mutual Funds']).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_savings_categories, remove_savings_categories),
    ] 