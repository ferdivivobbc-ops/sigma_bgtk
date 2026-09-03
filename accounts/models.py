from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin BGTK'
        PEMBIMBING = 'PEMBIMBING', 'Pembimbing BGTK'
        MAHASISWA = 'MAHASISWA', 'Mahasiswa'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MAHASISWA
    )
    no_hp = models.CharField(max_length=20, blank=True, null=True)

    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser

    def is_pembimbing(self):
        return self.role == self.Role.PEMBIMBING

    def is_mahasiswa(self):
        return self.role == self.Role.MAHASISWA

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class Notification(models.Model):
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=180)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class AuditLog(models.Model):
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    action = models.CharField(max_length=120)
    model_name = models.CharField(max_length=120, blank=True)
    object_id = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
