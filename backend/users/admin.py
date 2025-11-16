from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from datetime import timedelta
from django.conf import settings
from .models import UserProfile, PasswordResetToken

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profil'
    readonly_fields = [
        'total_quizzes_played',
        'total_questions_answered',
        'total_correct_answers',
        'highest_streak',
        'accuracy',
        'created_at',
        'updated_at'
    ]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'get_role', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_superuser', 'is_active', 'profile__role']
    search_fields = ['email', 'username']
    ordering = ['-date_joined']
    inlines = [UserProfileInline]

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Uprawnienia', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Ważne daty', {
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
        return obj.profile.role if hasattr(obj, 'profile') else 'N/A'

    get_role.short_description = 'Rola'
    get_role.admin_order_field = 'profile__role'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'role_badge', 'total_quizzes_played', 'accuracy_badge', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = [
        'user',
        'total_quizzes_played',
        'total_questions_answered',
        'total_correct_answers',
        'highest_streak',
        'accuracy',
        'created_at',
        'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        ('Użytkownik', {
            'fields': ('user',)
        }),
        ('Rola i Avatar', {
            'fields': ('role', 'avatar')
        }),
        ('Statystyki', {
            'fields': (
                'total_quizzes_played',
                'total_questions_answered',
                'total_correct_answers',
                'highest_streak',
                'accuracy'
            ),
            'classes': ('collapse',)
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'

    def role_badge(self, obj):
        colors = {
            'admin': '#dc3545',
            'user': '#007bff'
        }
        labels = {
            'admin': 'Administrator',
            'user': 'Użytkownik'
        }
        color = colors.get(obj.role, '#6c757d')
        label = labels.get(obj.role, obj.role)
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            label
        )

    role_badge.short_description = 'Rola'

    def accuracy_badge(self, obj):
        accuracy = obj.accuracy
        if accuracy >= 80:
            color = '#28a745'
        elif accuracy >= 50:
            color = '#ffc107'
        else:
            color = '#dc3545'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{:.1f}%</span>',
            color,
            accuracy
        )

    accuracy_badge.short_description = 'Skuteczność'


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'code', 'created_at', 'expires_at', 'status_badge']
    list_filter = ['used', 'created_at']
    search_fields = ['user__email', 'code']
    readonly_fields = ['user', 'code', 'created_at', 'expires_at_display', 'time_remaining']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informacje o tokenie', {
            'fields': ('user', 'code', 'used')
        }),
        ('Czas', {
            'fields': ('created_at', 'expires_at_display', 'time_remaining')
        }),
    )

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = 'Email użytkownika'
    user_email.admin_order_field = 'user__email'

    def expires_at(self, obj):
        timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 3600)
        expiry = obj.created_at + timedelta(seconds=timeout)
        return expiry.strftime('%Y-%m-%d %H:%M:%S')

    expires_at.short_description = 'Wygasa o'

    def expires_at_display(self, obj):
        timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 3600)
        expiry = obj.created_at + timedelta(seconds=timeout)
        return expiry

    expires_at_display.short_description = 'Wygasa o'

    def time_remaining(self, obj):
        if obj.used:
            return '❌ Użyty'

        from django.utils import timezone
        timeout = getattr(settings, 'PASSWORD_RESET_TIMEOUT', 3600)
        expiry = obj.created_at + timedelta(seconds=timeout)
        remaining = expiry - timezone.now()

        if remaining.total_seconds() <= 0:
            return '⏰ Wygasł'

        minutes = int(remaining.total_seconds() // 60)
        seconds = int(remaining.total_seconds() % 60)
        return f'⏳ {minutes}min {seconds}s'

    time_remaining.short_description = 'Pozostały czas'

    def status_badge(self, obj):
        if obj.is_valid():
            return format_html(
                '<span style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">✓ Ważny</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 3px;">✗ Nieważny</span>'
        )

    status_badge.short_description = 'Status'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['user', 'code', 'created_at', 'expires_at_display', 'time_remaining']
        return self.readonly_fields
