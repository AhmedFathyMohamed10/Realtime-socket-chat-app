from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'full_name', 'phone', 'is_online', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'is_online', 'created_at')
    search_fields = ('username', 'email', 'full_name', 'phone')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'full_name', 'birth_date', 'national_id', 'profile_image', 'is_online')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'phone', 'full_name', 'birth_date', 'national_id')
        }),
    )

admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)