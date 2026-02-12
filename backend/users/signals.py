import logging
from django.contrib.auth import get_user_model
from django.db.models.signals import post_delete, post_migrate, post_save, pre_save
from django.dispatch import receiver

from .models import UserProfile

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_migrate)
def create_default_users(sender, **kwargs):
    if sender.name != 'users':
        return
    logger.info('Creating default users')
    if not User.objects.filter(email='admin@quiz.com').exists():
        admin_user = User.objects.create_superuser(
            email='admin@quiz.com',
            username='admin',
            password='admin123'
        )
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()
        admin_user.profile.role = 'admin'
        admin_user.profile.save()
        logger.info('Admin user created (admin@quiz.com)')
    else:
        logger.info('Admin user already exists')
    if not User.objects.filter(email='user@quiz.com').exists():
        regular_user = User.objects.create_user(
            email='user@quiz.com',
            username='user',
            password='user123'
        )
        regular_user.is_active = True
        regular_user.save()
        regular_user.profile.role = 'user'
        regular_user.profile.save()
        logger.info('Regular user created (user@quiz.com)')
    else:
        logger.info('Regular user already exists')
    logger.info('Default users setup complete')

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(pre_save, sender=UserProfile)
def delete_old_avatar_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        previous_profile = UserProfile.objects.get(pk=instance.pk)
    except UserProfile.DoesNotExist:
        return

    previous_avatar = previous_profile.avatar
    current_avatar = instance.avatar

    previous_name = previous_avatar.name if previous_avatar else None
    current_name = current_avatar.name if current_avatar else None

    if previous_name and previous_name != current_name:
        previous_avatar.delete(save=False)


@receiver(post_delete, sender=UserProfile)
def delete_avatar_on_profile_delete(sender, instance, **kwargs):
    if instance.avatar:
        instance.avatar.delete(save=False)
