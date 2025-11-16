from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from users.models import UserProfile
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


@receiver(post_migrate)
def create_default_users(sender, **kwargs):
    if sender.name != 'users':
        return

    logger.info('Starting default users setup')

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

        logger.info('Admin user created: email=admin@quiz.com')
    else:
        logger.debug('Admin user already exists: email=admin@quiz.com')

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

        logger.info('Regular user created: email=user@quiz.com')
    else:
        logger.debug('Regular user already exists: email=user@quiz.com')

    logger.info('Default users setup completed')