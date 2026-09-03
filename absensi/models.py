from django.db import models
from mahasiswa.models import Mahasiswa

class Absensi(models.Model):
    class Status(models.TextChoices):
        HADIR = 'HADIR', 'Hadir'
        IZIN = 'IZIN', 'Izin'
        SAKIT = 'SAKIT', 'Sakit'
        ALPA = 'ALPA', 'Alpa'

    mahasiswa = models.ForeignKey(
        Mahasiswa,
        on_delete=models.CASCADE,
        related_name='absensi_list'
    )
    tanggal = models.DateField(verbose_name="Tanggal Absen")
    jam_masuk = models.TimeField(blank=True, null=True, verbose_name="Jam Masuk")
    jam_pulang = models.TimeField(blank=True, null=True, verbose_name="Jam Pulang")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.HADIR)
    latitude = models.CharField(max_length=50, blank=True, null=True, verbose_name="Latitude")
    longitude = models.CharField(max_length=50, blank=True, null=True, verbose_name="Longitude")
    foto_masuk = models.ImageField(upload_to='foto_absensi/', blank=True, null=True, verbose_name="Foto Masuk")
    foto_pulang = models.ImageField(upload_to='foto_absensi/', blank=True, null=True, verbose_name="Foto Pulang")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Absensi"
        ordering = ['-tanggal', '-jam_masuk']
        unique_together = ['mahasiswa', 'tanggal']

    def __str__(self):
        return f"Absensi {self.mahasiswa.nim} - {self.tanggal} ({self.status})"
