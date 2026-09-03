from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from datetime import date, timedelta, time
from accounts.models import User
from kampus.models import Kampus
from mahasiswa.models import Mahasiswa
from magang.models import Magang
from absensi.models import Absensi
from kegiatan.models import KegiatanHarian, KegiatanBulanan
from laporan.models import LaporanAkhir

class Command(BaseCommand):
    help = 'Seeds initial demo data for SIGMA BGTK Sumatera Barat'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Memulai seeding data demo SIGMA BGTK Sumatera Barat..."))

        # 1. Create Admin
        admin_user, created = User.objects.get_or_create(
            username='admin@sigma.test',
            defaults={
                'email': 'admin@sigma.test',
                'first_name': 'Admin',
                'last_name': 'BGTK Sumbar',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("[OK] Admin dibuat: admin@sigma.test / admin123"))
        else:
            self.stdout.write(self.style.SUCCESS("[OK] Admin sudah ada: admin@sigma.test"))

        # 2. Create Pembimbing
        pembimbing_user, created = User.objects.get_or_create(
            username='pembimbing@sigma.test',
            defaults={
                'email': 'pembimbing@sigma.test',
                'first_name': 'Dr. H. Pembimbing',
                'last_name': 'BGTK, M.Pd',
                'role': User.Role.PEMBIMBING,
                'no_hp': '081234567890'
            }
        )
        if created:
            pembimbing_user.set_password('pembimbing123')
            pembimbing_user.save()
            self.stdout.write(self.style.SUCCESS("[OK] Pembimbing dibuat: pembimbing@sigma.test / pembimbing123"))

        # 3. Create Campuses
        kampus_list = [
            ('Universitas Andalas', 'Fakultas Kedokteran, Fakultas Teknik, Fakultas Pertanian, Fakultas Ekonomi dan Bisnis, Fakultas Hukum', 'Teknik Informatika, Kedokteran, Agribisnis, Hukum, Manajemen', 'Limau Manis, Padang', '0751-71181'),
            ('Universitas Negeri Padang', 'Fakultas Teknik, Fakultas Ilmu Pendidikan, Fakultas Ekonomi, Fakultas Ilmu Sosial, Fakultas Matematika dan Ilmu Pengetahuan Alam', 'Pendidikan Teknik Informatika, Teknik Sipil, Manajemen, Pendidikan Bahasa Inggris, Pendidikan Matematika, Sistem Informasi', 'Jl. Prof. Dr. Hamka, Air Tawar, Padang', '0751-7053902'),
            ('Universitas Bung Hatta', 'Fakultas Teknik, Fakultas Ekonomi dan Bisnis, Fakultas Ilmu Sosial dan Politik', 'Teknik Sipil, Teknik Informatika, Akuntansi, Ilmu Komunikasi', 'Jl. Sumatera Ulak Karang, Padang', '0751-705123'),
            ('Universitas Muhammadiyah Sumatera Barat', 'Fakultas Keguruan dan Ilmu Pendidikan, Fakultas Teknik, Fakultas Ekonomi', 'Pendidikan Matematika, Teknik Informatika, Manajemen', 'Padang, Sumatera Barat', '0751-705000'),
            ('Universitas Ekasakti', 'Fakultas Hukum, Fakultas Ekonomi, Fakultas Pertanian', 'Hukum, Manajemen, Agribisnis', 'Padang, Sumatera Barat', '0751-123456'),
            ('Universitas Baiturrahmah', 'Fakultas Kedokteran, Fakultas Kedokteran Gigi, Fakultas Ekonomi dan Bisnis, Fakultas Kesehatan Masyarakat', 'Kedokteran, Kedokteran Gigi, Manajemen, Akuntansi, Kesehatan Masyarakat', 'Jl. Raya By Pass, Aie Pacah, Padang', '0751-463250'),
            ('Universitas Putra Indonesia YPTK Padang', 'Fakultas Teknik, Fakultas Ilmu Komputer, Fakultas Ekonomi dan Bisnis, Fakultas Psikologi', 'Teknik Informatika, Sistem Informasi, Manajemen, Akuntansi, Psikologi', 'Jl. Raya Lubuk Begalung, Padang', '0751-776666'),
            ('Universitas Dharma Andalas', 'Fakultas Ilmu Sosial, Fakultas Teknik, Fakultas Ekonomi', 'Teknik Informatika, Manajemen, Ilmu Komunikasi', 'Padang, Sumatera Barat', '0751-987654'),
            ('Universitas Tamansiswa Padang', 'Fakultas Ekonomi, Fakultas Hukum, Fakultas Pertanian, Fakultas Keguruan dan Ilmu Pendidikan', 'Manajemen, Akuntansi, Ilmu Hukum, Agroteknologi, Pendidikan Bahasa Indonesia', 'Jl. Tamansiswa No. 9, Padang', '0751-40020'),
            ('Universitas Adzkia', 'Fakultas Keguruan dan Ilmu Pendidikan, Fakultas Ekonomi dan Bisnis, Fakultas Teknik', 'Pendidikan Guru Sekolah Dasar, Pendidikan Bahasa Inggris, Manajemen, Teknik Informatika', 'Jl. Taratak Paneh No. 7, Korong Gadang, Padang', '0751-463250'),
            ('Universitas Fort De Kock', 'Fakultas Kesehatan, Fakultas Ekonomi dan Bisnis', 'Keperawatan, Kebidanan, Administrasi Rumah Sakit, Kewirausahaan', 'Jl. Soekarno Hatta No. 11, Bukittinggi', '0752-23222'),
            ('Universitas Mohammad Natsir', 'Fakultas Ekonomi dan Bisnis, Fakultas Ilmu Komputer, Fakultas Hukum', 'Manajemen, Akuntansi, Informatika, Sistem Informasi, Ilmu Hukum', 'Bukittinggi, Sumatera Barat', '0752-000000'),
            ('Universitas Mahaputra Muhammad Yamin Solok', 'Fakultas Keguruan dan Ilmu Pendidikan, Fakultas Ekonomi, Fakultas Teknik', 'Pendidikan Bahasa Indonesia, Manajemen, Teknik Informatika', 'Jl. Jendral Sudirman, Solok', '0755-20101'),
            ('Universitas Perintis Indonesia', 'Fakultas Ilmu Kesehatan, Fakultas Ekonomi dan Bisnis, Fakultas Sains dan Teknologi', 'Keperawatan, Farmasi, Gizi, Manajemen, Informatika', 'Jl. Adinegoro KM 17, Lubuk Buaya, Padang', '0751-484075'),
            ('Universitas PGRI Sumatera Barat', 'Fakultas Keguruan dan Ilmu Pendidikan, Fakultas Sains dan Teknologi, Fakultas Ekonomi dan Bisnis', 'Pendidikan Bahasa Indonesia, Pendidikan Matematika, Pendidikan Geografi, Informatika, Manajemen', 'Jl. Gunung Pangilun, Padang', '0751-7053731'),
            ('Universitas Nahdlatul Ulama Sumatera Barat', 'Fakultas Sains, Teknologi dan Pendidikan, Fakultas Ekonomi dan Bisnis', 'Informatika, Sistem Informasi, Pendidikan Guru Sekolah Dasar, Manajemen', 'Jl. S. Parman No. 119, Padang', '0751-7052000'),
            ('Universitas Islam Negeri Imam Bonjol Padang', 'Fakultas Adab dan Humaniora, Fakultas Dakwah, Fakultas Syariah, Fakultas Tarbiyah dan Keguruan, Fakultas Ushuluddin dan Studi Agama, Fakultas Ekonomi dan Bisnis Islam', 'Pendidikan Agama Islam, Hukum Ekonomi Syariah, Manajemen Perbankan Syariah, Komunikasi dan Penyiaran Islam', 'Jl. Prof. Mahmud Yunus, Lubuk Lintah, Padang', '0751-24435'),
            ('Universitas Islam Negeri Mahmud Yunus Batusangkar', 'Fakultas Tarbiyah dan Ilmu Keguruan, Fakultas Syariah, Fakultas Ekonomi dan Bisnis Islam', 'Pendidikan Agama Islam, Hukum Ekonomi Syariah, Perbankan Syariah, Manajemen Bisnis Syariah', 'Jl. Sudirman No. 137, Batusangkar, Tanah Datar', '0752-71150'),
            ('Universitas Islam Negeri Sjech M. Djamil Djambek Bukittinggi', 'Fakultas Tarbiyah dan Ilmu Keguruan, Fakultas Syariah, Fakultas Ekonomi dan Bisnis Islam', 'Pendidikan Agama Islam, Hukum Keluarga Islam, Perbankan Syariah, Manajemen Bisnis Syariah', 'Jl. Gurun Aua, Kubang Putih, Bukittinggi', '0752-33136'),
            ('Universitas Sumatera Barat', 'Fakultas Teknik, Fakultas Ekonomi dan Bisnis, Fakultas Ilmu Sosial dan Politik', 'Teknik Informatika, Teknik Sipil, Manajemen, Akuntansi, Ilmu Komunikasi', 'Padang, Sumatera Barat', '0751-555123'),
            ('Institut Teknologi Padang', 'Fakultas Teknik, Fakultas Teknologi Industri', 'Teknik Sipil, Teknik Mesin, Teknik Elektro, Teknik Informatika, Sistem Informasi', 'Jl. Gajah Mada Kandis Nanggalo, Padang', '0751-7055202'),
            ('Institut Seni Indonesia Padangpanjang', 'Fakultas Seni Pertunjukan, Fakultas Seni Rupa dan Desain', 'Seni Karawitan, Seni Tari, Seni Musik, Televisi dan Film, Kriya Seni, Desain Komunikasi Visual', 'Jl. Bahder Johan, Padangpanjang', '0752-82077'),
            ('Institut Agama Islam Negeri Bukittinggi', 'Fakultas Tarbiyah dan Ilmu Keguruan, Fakultas Syariah, Fakultas Ushuluddin', 'Pendidikan Agama Islam, Ekonomi Syariah, Komunikasi Penyiaran Islam', 'Bukittinggi, Sumatera Barat', '0752-22000'),
            ('Institut Agama Islam Negeri Batusangkar', 'Fakultas Tarbiyah dan Ilmu Keguruan, Fakultas Syariah, Fakultas Ekonomi dan Bisnis Islam', 'Pendidikan Agama Islam, Hukum Syariah, Manajemen Bisnis Syariah', 'Batusangkar, Sumatera Barat', '0752-71150'),
        ]

        kampus_list = [
            item for item in kampus_list
            if item[0].strip().lower().startswith(('universitas', 'institut'))
        ]

        Kampus.objects.exclude(
            Q(nama_kampus__istartswith='Universitas') |
            Q(nama_kampus__istartswith='Institut')
        ).delete()

        kampus_objects = {}
        for nama, fakultas, prodi, alamat, kontak in kampus_list:
            kampus_objects[nama], _ = Kampus.objects.get_or_create(
                nama_kampus=nama,
                defaults={'fakultas': fakultas, 'prodi': prodi, 'alamat': alamat, 'kontak': kontak, 'status': 'AKTIF'}
            )

        unp = Kampus.objects.get(nama_kampus='Universitas Negeri Padang')
        unand = Kampus.objects.get(nama_kampus='Universitas Andalas')
        self.stdout.write(self.style.SUCCESS("[OK] Master data kampus berhasil dibuat."))

        # 4. Create Mahasiswa 1
        mhs1_user, created = User.objects.get_or_create(
            username='mahasiswa@sigma.test',
            defaults={
                'email': 'mahasiswa@sigma.test',
                'first_name': 'Mahasiswa',
                'last_name': 'Demo',
                'role': User.Role.MAHASISWA,
                'no_hp': '0821987654321'
            }
        )
        if created:
            mhs1_user.set_password('mahasiswa123')
            mhs1_user.save()

        mhs1, _ = Mahasiswa.objects.get_or_create(
            user=mhs1_user,
            defaults={
                'kampus': unp,
                'nim': '220101001',
                'prodi': 'Pendidikan Teknik Informatika',
                'no_hp': '0821987654321',
                'status': 'AKTIF'
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Mahasiswa Demo dibuat: mahasiswa@sigma.test / mahasiswa123"))

        # Create Mahasiswa 2
        mhs2_user, created = User.objects.get_or_create(
            username='mahasiswa2@sigma.test',
            defaults={
                'email': 'mahasiswa2@sigma.test',
                'first_name': 'Siti',
                'last_name': 'Rahmawati',
                'role': User.Role.MAHASISWA,
                'no_hp': '081377889900'
            }
        )
        if created:
            mhs2_user.set_password('mahasiswa123')
            mhs2_user.save()

        mhs2, _ = Mahasiswa.objects.get_or_create(
            user=mhs2_user,
            defaults={
                'kampus': unand,
                'nim': '220101002',
                'prodi': 'Sistem Informasi',
                'no_hp': '081377889900',
                'status': 'AKTIF'
            }
        )

        # 5. Create Magang Placements
        today = date.today()
        start_date = today - timedelta(days=20)
        end_date = today + timedelta(days=40)

        magang1, _ = Magang.objects.get_or_create(
            mahasiswa=mhs1,
            defaults={
                'tanggal_mulai': start_date,
                'tanggal_selesai': end_date,
                'bagian': 'Subbagian Tata Usaha & IT Support',
                'pembimbing': pembimbing_user,
                'status': 'AKTIF'
            }
        )

        magang2, _ = Magang.objects.get_or_create(
            mahasiswa=mhs2,
            defaults={
                'tanggal_mulai': start_date,
                'tanggal_selesai': end_date,
                'bagian': 'Pengembangan & Pemberdayaan Pendidik',
                'pembimbing': pembimbing_user,
                'status': 'AKTIF'
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Data magang mahasiswa berhasil dikonfigurasi."))

        # 6. Seed Past Attendance records
        for i in range(15):
            past_date = today - timedelta(days=i)
            # Skip weekends (Saturday=5, Sunday=6)
            if past_date.weekday() in [5, 6]:
                continue
            
            Absensi.objects.get_or_create(
                mahasiswa=mhs1,
                tanggal=past_date,
                defaults={
                    'jam_masuk': time(8, 0, 0),
                    'jam_pulang': time(16, 30, 0),
                    'status': 'HADIR',
                    'latitude': '-0.9471',
                    'longitude': '100.3543'
                }
            )

        self.stdout.write(self.style.SUCCESS("[OK] Data absensi simulasi berhasil disemai."))

        # 7. Seed Daily Journals
        journals = [
            ("Orientasi Lingkungan Kerja BGTK Sumbar", "Pengenalan seluruh unit kerja dan penyerahan ke pembimbing lapang.", "Berhasil mengenal jajaran staf dan struktur organisasi.", "DISETUJUI"),
            ("Input Data Peserta Pelatihan Guru", "Penginputan data peserta pelatihan dari 19 kabupaten/kota ke spreadsheet.", "Data 150 peserta terdistribusi secara rapi.", "DISETUJUI"),
            ("Perawatan & Maintenance Server BGTK", "Pemeriksaan jaringan lokal (LAN) dan backup database SIGMA.", "Server berjalan stabil tanpa downtime.", "DISETUJUI"),
            ("Pengarsipan Berkas Administrasi Magang", "Merapikan berkas fisik absensi dan surat tugas magang.", "Berkas tersusun rapi di lemari arsip.", "PERLU_REVISI"),
            ("Penyusunan Draft Laporan Mingguan", "Membuat ringkasan kegiatan mingguan untuk diserahkan ke pembimbing.", "Draft awal telah selesai dibuat.", "MENUNGGU")
        ]

        for idx, (judul, uraian, hasil, st) in enumerate(journals):
            tgl = today - timedelta(days=idx*2)
            minggu_mulai = tgl - timedelta(days=tgl.weekday())
            kegiatan_obj, _ = KegiatanHarian.objects.get_or_create(
                mahasiswa=mhs1,
                tanggal=tgl,
                judul_kegiatan=judul,
                defaults={
                    'minggu_mulai': minggu_mulai,
                    'minggu_selesai': minggu_mulai + timedelta(days=6),
                    'kegiatan': uraian,
                    'hasil': hasil,
                    'kendala': 'Tidak ada kendala berarti',
                    'solusi': 'Berkoordinasi aktif dengan tim IT',
                    'status_verifikasi': st,
                    'komentar_pembimbing': 'Tingkatkan kualitas dokumentasi foto.' if st == 'PERLU_REVISI' else 'Bagus, lanjutkan.',
                    'verified_by': pembimbing_user if st == 'DISETUJUI' else None,
                    'verified_at': timezone.now() if st == 'DISETUJUI' else None
                }
            )
            if kegiatan_obj.minggu_mulai != minggu_mulai or kegiatan_obj.minggu_selesai != minggu_mulai + timedelta(days=6):
                kegiatan_obj.minggu_mulai = minggu_mulai
                kegiatan_obj.minggu_selesai = minggu_mulai + timedelta(days=6)
                kegiatan_obj.save(update_fields=['minggu_mulai', 'minggu_selesai'])

        self.stdout.write(self.style.SUCCESS("[OK] Jurnal kegiatan mingguan demo berhasil disemai."))

        # 8. Create Monthly Recap
        KegiatanBulanan.objects.get_or_create(
            mahasiswa=mhs1,
            bulan=today.month,
            tahun=today.year,
            defaults={
                'ringkasan': f"Rekapitulasi kegiatan bulan {today.month}/{today.year}. Kehadiran 100%. Berhasil menginput data peserta dan maintenance IT BGTK.",
                'total_hadir': 12,
                'total_kegiatan': 5,
                'total_disetujui': 3
            }
        )

        # 9. Create Laporan Akhir Draft
        LaporanAkhir.objects.get_or_create(
            mahasiswa=mhs1,
            defaults={
                'judul': 'LAPORAN AKHIR PRAKTEK KERJA LAPANGAN DI BGTK SUMATERA BARAT',
                'kata_pengantar': 'Puji syukur kehadirat Allah SWT. Laporan ini disusun atas pelaksanaan magang di BGTK Sumatera Barat.',
                'latar_belakang': 'BGTK Sumatera Barat memiliki peran strategis dalam peningkatan mutu pendidik.',
                'tujuan': '1. Memahami tata kelola IT BGTK Sumbar.\n2. Mengembangkan keterampilan teknis.',
                'manfaat': 'Memberikan pengalaman praktis dalam lingkungan kerja profesional.',
                'gambaran_umum': 'BGTK Sumbar bertugas melaksanakan pengembangan dan pemberdayaan guru.',
                'pelaksanaan_magang': 'Magang dilaksanakan pada unit Subbagian Tata Usaha & IT Support.',
                'hasil_pembahasan': 'Telah berhasil menyelesaikan tugas administrasi dan maintenance infrastruktur.',
                'kesimpulan': 'Magang berjalan efektif dan menambah kompetensi mahasiswa secara nyata.',
                'saran': 'Agar komunikasi antara kampus dan instansi terus ditingkatkan.',
                'status': 'DRAFT'
            }
        )

        self.stdout.write(self.style.SUCCESS("\n=================================================="))
        self.stdout.write(self.style.SUCCESS("  DATA DEMO BERHASIL DI-SEED UNTUK SIGMA BGTK!   "))
        self.stdout.write(self.style.SUCCESS("=================================================="))
        self.stdout.write("Akun Pengujian:")
        self.stdout.write("1. ADMIN      : admin@sigma.test / admin123")
        self.stdout.write("2. PEMBIMBING : pembimbing@sigma.test / pembimbing123")
        self.stdout.write("3. MAHASISWA  : mahasiswa@sigma.test / mahasiswa123")
        self.stdout.write("==================================================\n")
