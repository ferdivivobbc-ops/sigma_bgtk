from datetime import date, timedelta

from django.test import TestCase

from accounts.models import User
from kegiatan.models import KegiatanHarian
from mahasiswa.models import Mahasiswa
from magang.models import Magang


class KegiatanWorkflowTests(TestCase):
    def setUp(self):
        self.pembimbing = User.objects.create_user(
            username='pembimbing-test', password='password123', role=User.Role.PEMBIMBING,
            first_name='Pembimbing'
        )
        self.mahasiswa_user = User.objects.create_user(
            username='mahasiswa-test', password='password123', role=User.Role.MAHASISWA,
            first_name='Mahasiswa'
        )
        self.mahasiswa = Mahasiswa.objects.create(
            user=self.mahasiswa_user, nim='TEST001', prodi='Informatika', status='AKTIF'
        )
        Magang.objects.create(
            mahasiswa=self.mahasiswa,
            tanggal_mulai=date.today() - timedelta(days=7),
            tanggal_selesai=date.today() + timedelta(days=30),
            bagian='Unit Test', pembimbing=self.pembimbing, status='AKTIF'
        )
        self.kegiatan = KegiatanHarian.objects.create(
            mahasiswa=self.mahasiswa,
            tanggal=date.today(),
            minggu_mulai=date.today() - timedelta(days=date.today().weekday()),
            minggu_selesai=date.today() + timedelta(days=6 - date.today().weekday()),
            judul_kegiatan='Kegiatan Uji', kegiatan='Uraian awal', hasil='Hasil awal',
            status_verifikasi='PERLU_REVISI'
        )

    def test_pembimbing_can_save_verification(self):
        self.client.login(username='pembimbing-test', password='password123')
        response = self.client.post(f'/kegiatan/{self.kegiatan.pk}/verifikasi/', {
            'status_verifikasi': 'DISETUJUI',
            'komentar_pembimbing': 'Sudah baik.',
        })
        self.assertRedirects(response, '/kegiatan/', fetch_redirect_response=False)
        self.kegiatan.refresh_from_db()
        self.assertEqual(self.kegiatan.status_verifikasi, 'DISETUJUI')
        self.assertEqual(self.kegiatan.komentar_pembimbing, 'Sudah baik.')

    def test_student_can_edit_revision(self):
        self.client.login(username='mahasiswa-test', password='password123')
        response = self.client.post(f'/kegiatan/{self.kegiatan.pk}/edit/', {
            'tanggal': date.today().isoformat(),
            'minggu_mulai': date.today().isoformat(),
            'judul_kegiatan': 'Kegiatan Diperbarui',
            'kegiatan': 'Uraian diperbarui',
            'hasil': 'Hasil diperbarui',
            'kendala': 'Tidak ada',
            'solusi': 'Tidak ada',
        })
        self.assertRedirects(response, f'/kegiatan/{self.kegiatan.pk}/', fetch_redirect_response=False)
        self.kegiatan.refresh_from_db()
        self.assertEqual(self.kegiatan.status_verifikasi, 'MENUNGGU')
        self.assertEqual(self.kegiatan.judul_kegiatan, 'Kegiatan Diperbarui')