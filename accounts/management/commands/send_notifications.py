"""
Management command untuk mengirim notifications ke users
Usage:
    python manage.py send_notifications
    python manage.py send_notifications --type=verification_reminder
    python manage.py send_notifications --type=magang_status
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from kegiatan.models import KegiatanHarian
from utils.email_notifier import send_verification_reminder

User = get_user_model()


class Command(BaseCommand):
    help = 'Send notifications to users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='verification_reminder',
            help='Type of notification to send'
        )
        parser.add_argument(
            '--to-user',
            type=int,
            help='Send to specific user ID'
        )

    def handle(self, *args, **options):
        notification_type = options['type']
        to_user = options.get('to_user')

        if notification_type == 'verification_reminder':
            self.send_verification_reminders(to_user)
        else:
            self.stdout.write(self.style.ERROR(f'Unknown notification type: {notification_type}'))

    def send_verification_reminders(self, user_id=None):
        """Kirim reminder ke pembimbing tentang kegiatan menunggu verifikasi"""
        from django.contrib.auth.models import Group

        # Get all pembimbing users
        try:
            pembimbing_group = Group.objects.get(name='Pembimbing')
            pembimbing_users = pembimbing_group.user_set.all()
        except Group.DoesNotExist:
            # Fallback: get users dengan is_staff=True
            pembimbing_users = User.objects.filter(is_staff=True)

        if user_id:
            pembimbing_users = pembimbing_users.filter(id=user_id)

        sent_count = 0
        failed_count = 0

        for pembimbing in pembimbing_users:
            # Check if there are pending kegiatan for this pembimbing
            pending_count = KegiatanHarian.objects.filter(
                mahasiswa__data_magang__pembimbing=pembimbing,
                status_verifikasi='MENUNGGU'
            ).count()

            if pending_count > 0:
                try:
                    if send_verification_reminder(pembimbing):
                        sent_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Reminder sent to {pembimbing.get_full_name()} ({pending_count} pending kegiatan)'
                            )
                        )
                    else:
                        failed_count += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'✗ Failed to send reminder to {pembimbing.get_full_name()}'
                            )
                        )
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Error sending reminder to {pembimbing.get_full_name()}: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Total notifications sent: {sent_count}, Failed: {failed_count}'
            )
        )
