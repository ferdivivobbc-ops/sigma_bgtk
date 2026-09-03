from django.db import models
from django.conf import settings
from datetime import date
from mahasiswa.models import Mahasiswa

class Magang(models.Model):
    class Status(models.TextChoices):
        BELUM_MULAI = 'BELUM_MULAI', 'Belum Mulai'
        AKTIF = 'AKTIF', 'Aktif'
        SELESAI = 'SELESAI', 'Selesai'
        DIBATALKAN = 'DIBATALKAN', 'Dibatalkan'

    mahasiswa = models.OneToOneField(
        Mahasiswa,
        on_delete=models.CASCADE,
        related_name='data_magang'
    )
    tanggal_mulai = models.DateField(verbose_name="Tanggal Mulai")
    tanggal_selesai = models.DateField(verbose_name="Tanggal Selesai")
    bagian = models.CharField(max_length=150, verbose_name="Bagian / Unit BGTK")
    pembimbing = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bimbingan_magang_set',
        limit_choices_to={'role': 'PEMBIMBING'}
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AKTIF)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Data Magang"
        ordering = ['-tanggal_mulai']

    @property
    def progress_percentage(self):
        today = date.today()
        if today < self.tanggal_mulai:
            return 0
        if today >= self.tanggal_selesai or self.status == self.Status.SELESAI:
            return 100
        total_days = (self.tanggal_selesai - self.tanggal_mulai).days
        if total_days <= 0:
            return 100
        elapsed_days = (today - self.tanggal_mulai).days
        progress = int((elapsed_days / total_days) * 100)
        return min(100, max(0, progress))

    def __str__(self):
        return f"Magang {self.mahasiswa} - {self.bagian}"
