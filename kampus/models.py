from django.db import models

class Kampus(models.Model):
    class Status(models.TextChoices):
        AKTIF = 'AKTIF', 'Aktif'
        NONAKTIF = 'NONAKTIF', 'Nonaktif'

    nama_kampus = models.CharField(max_length=255, verbose_name="Nama Kampus")
    fakultas = models.TextField(blank=True, null=True, verbose_name="Fakultas")
    prodi = models.TextField(blank=True, null=True, verbose_name="Program Studi")
    alamat = models.TextField(blank=True, null=True, verbose_name="Alamat")
    kontak = models.CharField(max_length=100, blank=True, null=True, verbose_name="Kontak / Telepon")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.AKTIF)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Kampus"
        ordering = ['nama_kampus']

    def __str__(self):
        return self.nama_kampus
