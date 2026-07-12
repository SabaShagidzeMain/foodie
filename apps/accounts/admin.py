from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom admin for User model"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'dietary_pref', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'dietary_pref')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('dietary_pref', 'profile_picture', 'bio'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('dietary_pref',),
        }),
    )