"""
Utility untuk mengirim email notifications
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Class untuk mengirim email notifications"""
    
    DEFAULT_FROM_EMAIL = settings.DEFAULT_FROM_EMAIL or 'noreply@sigma-bgtk.local'
    
    @staticmethod
    def send_simple_email(subject, message, recipient_list, from_email=None):
        """Kirim email sederhana (plain text)"""
        try:
            if not from_email:
                from_email = EmailNotifier.DEFAULT_FROM_EMAIL
            
            send_mail(
                subject,
                message,
                from_email,
                recipient_list,
                fail_silently=False,
            )
            logger.info(f"Email '{subject}' terkirim ke {recipient_list}")
            return True
        except Exception as e:
            logger.error(f"Gagal mengirim email: {str(e)}")
            return False
    
    @staticmethod
    def send_html_email(subject, template_name, context, recipient_list, from_email=None):
        """Kirim email dengan HTML template"""
        try:
            if not from_email:
                from_email = EmailNotifier.DEFAULT_FROM_EMAIL
            
            # Render HTML dari template
            html_message = render_to_string(template_name, context)
            text_message = strip_tags(html_message)
            
            # Buat email dengan both plain text dan HTML
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_message,
                from_email=from_email,
                to=recipient_list
            )
            email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"HTML Email '{subject}' terkirim ke {recipient_list}")
            return True
        except Exception as e:
            logger.error(f"Gagal mengirim HTML email: {str(e)}")
            return False


# Template specific email senders
def send_verification_reminder(user):
    """Kirim reminder ke pembimbing untuk verifikasi kegiatan"""
    pending_count = user.verified_kegiatan_set.filter(
        kegiatan_harian__status_verifikasi='MENUNGGU'
    ).count()
    
    if pending_count == 0:
        return False
    
    subject = f"[SIGMA] Reminder: Ada {pending_count} Kegiatan Mahasiswa Menunggu Verifikasi"
    message = f"""
Halo {user.get_full_name()},

Anda memiliki {pending_count} kegiatan mingguan mahasiswa yang menunggu verifikasi di sistem SIGMA BGTK.

Mohon segera lakukan verifikasi melalui: {settings.SITE_URL or 'https://sigma.bgtk.id'}

Terima kasih,
SIGMA BGTK Sumatera Barat
"""
    
    return EmailNotifier.send_simple_email(
        subject=subject,
        message=message,
        recipient_list=[user.email],
    )


def send_kegiatan_status_notification(mahasiswa, kegiatan, status):
    """Kirim notifikasi ke mahasiswa tentang status kegiatan"""
    subject = f"[SIGMA] Status Kegiatan: {kegiatan.judul_kegiatan} - {status}"
    message = f"""
Halo {mahasiswa.user.get_full_name()},

Kegiatan mingguan Anda dengan judul "{kegiatan.judul_kegiatan}" pada tanggal {kegiatan.tanggal.strftime('%d-%m-%Y')} 
telah {status.lower()}.

"""
    
    if status == 'DISETUJUI':
        message += "Kegiatan Anda telah diterima oleh pembimbing."
    elif status == 'DITOLAK':
        message += "Kegiatan Anda ditolak. Silakan pelajari komentar pembimbing dan lakukan perbaikan."
    elif status == 'PERLU_REVISI':
        message += "Kegiatan Anda perlu diperbaiki. Silakan lihat komentar pembimbing dan lakukan perbaikan."
    
    if kegiatan.komentar_pembimbing:
        message += f"\n\nKomentar Pembimbing:\n{kegiatan.komentar_pembimbing}"
    
    message += f"\n\nTanggal Verifikasi: {kegiatan.verified_at.strftime('%d-%m-%Y %H:%M') if kegiatan.verified_at else '-'}"
    message += "\n\nTerima kasih,\nSIGMA BGTK Sumatera Barat"
    
    return EmailNotifier.send_simple_email(
        subject=subject,
        message=message,
        recipient_list=[mahasiswa.user.email],
    )


def send_magang_status_notification(mahasiswa, magang, status):
    """Kirim notifikasi ke mahasiswa tentang status magang"""
    subject = f"[SIGMA] Status Magang: {status}"
    message = f"""
Halo {mahasiswa.user.get_full_name()},

Status magang Anda telah berubah menjadi: {status}

Periode Magang: {magang.tanggal_mulai.strftime('%d-%m-%Y')} s/d {magang.tanggal_selesai.strftime('%d-%m-%Y')}
Bagian/Unit: {magang.bagian or '-'}
Pembimbing: {magang.pembimbing.get_full_name() if magang.pembimbing else '-'}

Silakan login ke sistem untuk informasi lebih detail.

Terima kasih,
SIGMA BGTK Sumatera Barat
"""
    
    return EmailNotifier.send_simple_email(
        subject=subject,
        message=message,
        recipient_list=[mahasiswa.user.email],
    )


def send_absensi_notification(mahasiswa, tanggal, status):
    """Kirim notifikasi absensi ke mahasiswa"""
    subject = f"[SIGMA] Konfirmasi Absensi - {status}"
    message = f"""
Halo {mahasiswa.user.get_full_name()},

Absensi Anda pada tanggal {tanggal.strftime('%d-%m-%Y')} telah dicatat dengan status: {status}

Terima kasih,
SIGMA BGTK Sumatera Barat
"""
    
    return EmailNotifier.send_simple_email(
        subject=subject,
        message=message,
        recipient_list=[mahasiswa.user.email],
    )


def send_bulk_notification(subject, message, recipient_list):
    """Kirim notifikasi bulk ke multiple recipients"""
    return EmailNotifier.send_simple_email(
        subject=subject,
        message=message,
        recipient_list=recipient_list,
    )
