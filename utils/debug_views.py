"""
Utility views untuk testing dan debugging
"""
from django.shortcuts import render, HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.conf import settings

from utils.email_notifier import send_verification_reminder, EmailNotifier


@login_required
def test_send_email(request):
    """Test send email functionality (Admin only)"""
    if not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)
    
    if request.method == 'POST':
        recipient_email = request.POST.get('email')
        email_type = request.POST.get('type', 'simple')
        
        if email_type == 'simple':
            success = EmailNotifier.send_simple_email(
                subject="[SIGMA] Test Email",
                message="Ini adalah test email dari SIGMA BGTK Sumatera Barat. Jika Anda menerima email ini, berarti konfigurasi email sudah berfungsi dengan baik.",
                recipient_list=[recipient_email]
            )
        elif email_type == 'verification':
            user = User.objects.filter(email=recipient_email).first()
            if user:
                success = send_verification_reminder(user)
            else:
                success = False
        else:
            success = False
        
        if success:
            return HttpResponse(f"✓ Email berhasil dikirim ke {recipient_email}")
        else:
            return HttpResponse(f"✗ Gagal mengirim email ke {recipient_email}", status=500)
    
    return render(request, 'admin/test_email.html')


def email_config_info(request):
    """Display email configuration info (for debugging)"""
    if not request.user.is_staff:
        return HttpResponse("Unauthorized", status=403)
    
    config = {
        'EMAIL_BACKEND': settings.EMAIL_BACKEND,
        'EMAIL_HOST': settings.EMAIL_HOST,
        'EMAIL_PORT': settings.EMAIL_PORT,
        'EMAIL_USE_TLS': settings.EMAIL_USE_TLS,
        'EMAIL_HOST_USER': settings.EMAIL_HOST_USER,
        'DEFAULT_FROM_EMAIL': settings.DEFAULT_FROM_EMAIL,
        'DEBUG': settings.DEBUG,
    }
    
    return render(request, 'admin/email_config.html', {'config': config})
