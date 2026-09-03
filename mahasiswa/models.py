from django.db import models
from django.conf import settings
from kampus.models import Kampus

class Mahasiswa(models.Model):
    class Status(models.TextChoices):
        AKTIF = 'AKTIF', 'Aktif'
        SELESAI = 'SELESAI', 'Selesai'
        NONAKTIF = 'NONAKTIF', 'Nonaktif'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mahasiswa_profile'
    )
    kampus = models.ForeignKey(
        Kampus,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='mahasiswa_list'
    )
    nim = models.CharField(max_length=50, unique=True, verbose_name="NIM")
    prodi = models.CharField(max_length=150, verbose_name="Program Studi")
    no_hp = models.CharField(max_length=20, blank=True, null=True, verbose_name="Nomor HP")
    foto = models.ImageField(upload_to='foto_mahasiswa/', blank=True, null=True, verbose_name="Foto Profile")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AKTIF)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Mahasiswa"
        ordering = ['user__first_name', 'nim']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.nim})"
