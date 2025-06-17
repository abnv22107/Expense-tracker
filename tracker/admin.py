from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Category, Expense, Income, UserProfile

# Register UserProfile as inline with User
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'

# Extend UserAdmin to include UserProfile
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at', 'updated_at')
    list_filter = ('user', 'created_at')
    search_fields = ('name',)
    date_hierarchy = 'created_at'
    ordering = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'category', 'date', 'user', 'created_at')
    list_filter = ('category', 'date', 'user', 'created_at')
    search_fields = ('description', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date', '-created_at')
    list_per_page = 20

@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('description', 'amount', 'category', 'date', 'user', 'created_at')
    list_filter = ('category', 'date', 'user', 'created_at')
    search_fields = ('description', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date', '-created_at')
    list_per_page = 20

# Customize admin site
admin.site.site_header = 'Expense Tracker Administration'
admin.site.site_title = 'Expense Tracker Admin'
admin.site.index_title = 'Welcome to Expense Tracker Admin'
