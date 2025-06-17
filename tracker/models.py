from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='categories'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        unique_together = ['name', 'user']  # Allow same category name for different users

    def __str__(self):
        return self.name

class Expense(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='expenses'
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='expenses'
    )
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} - ₹{self.amount}"

    def save(self, *args, **kwargs):
        # If no category is set, create or get an "Uncategorized" category
        if not self.category:
            uncategorized, created = Category.objects.get_or_create(
                name="Uncategorized",
                user=self.user
            )
            self.category = uncategorized
        super().save(*args, **kwargs)

class Income(models.Model):
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.now)
    category = models.CharField(max_length=100, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.description} - ₹{self.amount}"

class UserProfile(models.Model):
    RISK_TOLERANCE_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    INVESTMENT_GOAL_CHOICES = [
        ('wealth_creation', 'Wealth Creation'),
        ('tax_saving', 'Tax Saving'),
        ('short_term_goal', 'Short Term Goal'),
        ('retirement', 'Retirement'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    risk_tolerance = models.CharField(max_length=10, choices=RISK_TOLERANCE_CHOICES, default='medium')
    investment_goal = models.CharField(max_length=20, choices=INVESTMENT_GOAL_CHOICES, default='wealth_creation')
    investment_horizon_years = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
