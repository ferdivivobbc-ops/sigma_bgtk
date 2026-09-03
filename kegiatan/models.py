from django.db import models
from django.conf import settings
from mahasiswa.models import Mahasiswa

class KegiatanHarian(models.Model):
    class StatusVerifikasi(models.TextChoices):
        MENUNGGU = 'MENUNGGU', 'Menunggu'
        DISETUJUI = 'DISETUJUI', 'Disetujui'
        DITOLAK = 'DITOLAK', 'Ditolak'
        PERLU_REVISI = 'PERLU_REVISI', 'Perlu Revisi'

    mahasiswa = models.ForeignKey(
        Mahasiswa,
        on_delete=models.CASCADE,
        related_name='kegiatan_harian_list'
    )
    tanggal = models.DateField(verbose_name="Tanggal Kegiatan")
    minggu_mulai = models.DateField(blank=True, null=True, verbose_name="Minggu Mulai")
    minggu_selesai = models.DateField(blank=True, null=True, verbose_name="Minggu Selesai")
    judul_kegiatan = models.CharField(max_length=200, verbose_name="Judul Kegiatan")
    kegiatan = models.TextField(verbose_name="Uraian Kegiatan")
    hasil = models.TextField(verbose_name="Hasil Kegiatan")
    kendala = models.TextField(blank=True, default="Tidak ada kendala", verbose_name="Kendala")
    solusi = models.TextField(blank=True, default="Tidak ada", verbose_name="Solusi")
    dokumentasi = models.ImageField(
        upload_to='dokumentasi_kegiatan/',
        blank=True,
        null=True,
        verbose_name="Dokumentasi Foto"
    )
    status_verifikasi = models.CharField(
        max_length=20,
        choices=StatusVerifikasi.choices,
        default=StatusVerifikasi.MENUNGGU
    )
    komentar_pembimbing = models.TextField(blank=True, null=True, verbose_name="Komentar Pembimbing")
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_kegiatan_set'
    )
    verified_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Kegiatan Mingguan"
        ordering = ['-tanggal', '-created_at']

    def __str__(self):
        return f"{self.mahasiswa.user.get_full_name()} - {self.judul_kegiatan} ({self.tanggal})"


class KegiatanBulanan(models.Model):
    mahasiswa = models.ForeignKey(
        Mahasiswa,
        on_delete=models.CASCADE,
        related_name='rekap_bulanan_list'
    )
    bulan = models.IntegerField(verbose_name="Bulan (1-12)")
    tahun = models.IntegerField(verbose_name="Tahun")
    ringkasan = models.TextField(verbose_name="Ringkasan Kegiatan Bulanan")
    total_hadir = models.IntegerField(default=0)
    total_kegiatan = models.IntegerField(default=0)
    total_disetujui = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Kegiatan Bulanan"
        ordering = ['-tahun', '-bulan']
        unique_together = ['mahasiswa', 'bulan', 'tahun']

    def __str__(self):
        return f"Rekap {self.mahasiswa.user.get_full_name()} - {self.bulan}/{self.tahun}"
