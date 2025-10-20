from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from datetime import timedelta
from django.conf import settings
from .models import UserProfile, PasswordResetToken

User = get_user_model()


# ==================== USER ADMIN ====================

class UserProfileInline(admin.StackedInline):
    """Inline profile w User admin"""
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    readonly_fields = ['total_quizzes_played', 'total_questions_answered',
                       'total_correct_answers', 'highest_streak', 'accuracy',
                       'created_at', 'updated_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin dla custom User model"""
    list_display = ['email', 'username', 'get_role', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'profile__role']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']
    inlines = [UserProfileInline]

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_active')
        }),
    )

    def get_role(self, obj):
        """Pokaż rolę w liście"""
        return obj.profile.role if hasattr(obj, 'profile') else 'N/A'

    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'


# ==================== USER PROFILE ADMIN ====================

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin dla UserProfile"""
    list_display = ['user_email', 'role', 'total_quizzes_played', 'accuracy', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['user', 'total_quizzes_played', 'total_questions_answered',
                       'total_correct_answers', 'highest_streak', 'accuracy',
                       'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Role & Avatar', {
            'fields': ('role', 'avatar')
        }),
        ('Statistics', {
            'fields': ('total_quizzes_played', 'total_questions_answered',
                       'total_correct_answers', 'highest_streak', 'accuracy'),
            'classes': ('collapse',)  # Domyślnie zwinięte
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        """Pokaż email użytkownika"""
        return obj.user.email

    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'


# ==================== PASSWORD RESET TOKEN ADMIN ====================

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin dla Password Reset Tokens"""
    list_display = ['user_email', 'code', 'created_at', 'expires_at', 'used', 'is_valid_display']
    list_filter = ['used', 'created_at']
    search_fields = ['user__email', 'code']
    readonly_fields = ['user', 'code', 'created_at', 'expires_at', 'time_remaining']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Token Info', {
            'fields': ('user', 'code', 'used')
        }),
        ('Timing', {
            'fields': ('created_at', 'expires_at', 'time_remaining')
        }),
    )

    def user_email(self, obj):
        """Pokaż email użytkownika"""
        return obj.user.email

    user_email.short_description = 'User Email'
    user_email.admin_order_field = 'user__email'

    def expires_at(self, obj):
        """Pokaż kiedy token wygasa"""
        timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 3600)
        expiry = obj.created_at + timedelta(seconds=timeout)
        return expiry.strftime('%Y-%m-%d %H:%M:%S')

    expires_at.short_description = 'Expires At'

    def time_remaining(self, obj):
        """Pokaż ile czasu zostało do wygaśnięcia"""
        if obj.used:
            return '❌ Used'

        from django.utils import timezone
        timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 3600)
        expiry = obj.created_at + timedelta(seconds=timeout)
        remaining = expiry - timezone.now()

        if remaining.total_seconds() <= 0:
            return '⏰ Expired'

        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        return f'⏳ {minutes}m {seconds}s remaining'

    time_remaining.short_description = 'Time Remaining'

    def is_valid_display(self, obj):
        """Pokaż czy token jest ważny (z ikoną)"""
        if obj.is_valid():
            return '✅ Valid'
        return '❌ Invalid'

    is_valid_display.short_description = 'Status'
    is_valid_display.admin_order_field = 'used'

    def has_add_permission(self, request):
        """Nie pozwól dodawać tokenów ręcznie - tylko przez API"""
        return False

    def has_change_permission(self, request, obj=None):
        """Pozwól tylko na zmianę statusu 'used'"""
        return True

    def get_readonly_fields(self, request, obj=None):
        """Wszystkie pola readonly oprócz 'used'"""
        if obj:  # Editing existing
            return ['user', 'code', 'created_at', 'expires_at', 'time_remaining']
        return self.readonly_fields