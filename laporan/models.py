from django.db import models
from mahasiswa.models import Mahasiswa

class LaporanAkhir(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        PERIKSA = 'PERIKSA', 'Menunggu Pemeriksaan'
        DISETUJUI = 'DISETUJUI', 'Disetujui'
        PERLU_REVISI = 'PERLU_REVISI', 'Perlu Revisi'

    mahasiswa = models.OneToOneField(
        Mahasiswa,
        on_delete=models.CASCADE,
        related_name='laporan_akhir'
    )
    judul = models.CharField(max_length=255, verbose_name="Judul Laporan Akhir")
    kata_pengantar = models.TextField(blank=True, null=True, verbose_name="Kata Pengantar")
    latar_belakang = models.TextField(blank=True, null=True, verbose_name="BAB I - Latar Belakang")
    tujuan = models.TextField(blank=True, null=True, verbose_name="BAB I - Tujuan Magang")
    manfaat = models.TextField(blank=True, null=True, verbose_name="BAB I - Manfaat Magang")
    gambaran_umum = models.TextField(blank=True, null=True, verbose_name="BAB II - Gambaran Umum BGTK Sumbar")
    pelaksanaan_magang = models.TextField(blank=True, null=True, verbose_name="BAB III - Pelaksanaan Magang")
    hasil_pembahasan = models.TextField(blank=True, null=True, verbose_name="BAB IV - Hasil & Pembahasan")
    kesimpulan = models.TextField(blank=True, null=True, verbose_name="BAB V - Kesimpulan")
    saran = models.TextField(blank=True, null=True, verbose_name="BAB V - Saran")
    
    file_pdf = models.FileField(upload_to='laporan/pdf/', blank=True, null=True, verbose_name="File PDF")
    file_word = models.FileField(upload_to='laporan/word/', blank=True, null=True, verbose_name="File Word (.docx)")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    catatan_pembimbing = models.TextField(blank=True, null=True, verbose_name="Catatan Pembimbing")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Laporan Akhir"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Laporan Akhir {self.mahasiswa.user.get_full_name()} - {self.judul}"
