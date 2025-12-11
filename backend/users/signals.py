import logging
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


@receiver(post_migrate)
def create_default_users(sender, **kwargs):
    """Automatyczne tworzenie admin i user po migracji"""

    if sender.name != 'users':
        return

    logger.info('=' * 60)
    logger.info('CREATING DEFAULT USERS')
    logger.info('=' * 60)

    # Admin user
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

        logger.info('Admin user created! Email: admin@quiz.com, Password: admin123')
    else:
        logger.warning('Admin user already exists')

    # Regular user
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

        logger.info('Regular user created! Email: user@quiz.com, Password: user123')
    else:
        logger.warning('Regular user already exists')

    logger.info('=' * 60)
    logger.info('DEFAULT USERS SETUP COMPLETE!')
    logger.info('=' * 60)