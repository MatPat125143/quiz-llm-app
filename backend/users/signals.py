from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_migrate)
def create_default_users(sender, **kwargs):
    """Automatyczne tworzenie admin i user po migracji"""

    if sender.name != 'users':
        return

    print('\n' + '=' * 60)
    print('🔧 CREATING DEFAULT USERS')
    print('=' * 60)

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

        print('✅ Admin user created!')
        print(f'   Email: admin@quiz.com')
        print(f'   Password: admin123\n')
    else:
        print('⚠️  Admin user already exists\n')

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

        print('✅ Regular user created!')
        print(f'   Email: user@quiz.com')
        print(f'   Password: user123\n')
    else:
        print('⚠️  Regular user already exists\n')

    print('=' * 60)
    print('🎉 DEFAULT USERS SETUP COMPLETE!')
    print('=' * 60 + '\n')