from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from accounts import views as accounts_views
from kampus import views as kampus_views
from mahasiswa import views as mahasiswa_views
from magang import views as magang_views
from absensi import views as absensi_views
from kegiatan import views as kegiatan_views
from laporan import views as laporan_views
from laporan.export_views import (
    export_mahasiswa_excel,
    export_absensi_excel,
    export_kegiatan_excel,
    export_magang_excel,
    export_rekap_kegiatan_bulanan_excel
)

urlpatterns = [
    path('django-admin/', admin.site.urls),

    # Authentication & Dashboard
    path('', accounts_views.dashboard_view, name='dashboard'),
    path('login/', accounts_views.login_view, name='login'),
    path('login/google/', accounts_views.google_login_view, name='google_login'),
    path('login/google/callback/', accounts_views.google_callback_view, name='google_callback'),
    path('logout/', accounts_views.logout_view, name='logout'),
    path('profile/', accounts_views.profile_view, name='profile'),
    path('profile/password/', accounts_views.password_change_view, name='password_change'),
    path('notifications/', accounts_views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', accounts_views.notification_read, name='notification_read'),
    path('notifications/read-all/', accounts_views.notifications_mark_all_read, name='notifications_mark_all_read'),
    path('audit-log/', accounts_views.audit_log_view, name='audit_log'),
    path('pembimbing/', accounts_views.pembimbing_list, name='pembimbing_list'),
    path('pembimbing/create/', accounts_views.pembimbing_create, name='pembimbing_create'),
    path('pembimbing/<int:pk>/delete/', accounts_views.pembimbing_delete, name='pembimbing_delete'),

    # Master Data Kampus
    path('kampus/', kampus_views.kampus_list, name='kampus_list'),
    path('kampus/create/', kampus_views.kampus_create, name='kampus_create'),
    path('kampus/<int:pk>/edit/', kampus_views.kampus_edit, name='kampus_edit'),
    path('kampus/<int:pk>/delete/', kampus_views.kampus_delete, name='kampus_delete'),

    # Master Data Mahasiswa
    path('mahasiswa/', mahasiswa_views.mahasiswa_list, name='mahasiswa_list'),
    path('mahasiswa/<int:pk>/', mahasiswa_views.mahasiswa_detail, name='mahasiswa_detail'),
    path('mahasiswa/create/', mahasiswa_views.mahasiswa_create, name='mahasiswa_create'),
    path('mahasiswa/import/', mahasiswa_views.mahasiswa_import, name='mahasiswa_import'),
    path('mahasiswa/<int:pk>/edit/', mahasiswa_views.mahasiswa_edit, name='mahasiswa_edit'),
    path('mahasiswa/<int:pk>/delete/', mahasiswa_views.mahasiswa_delete, name='mahasiswa_delete'),

    # Modul Magang
    path('magang/', magang_views.magang_list, name='magang_list'),
    path('magang/create/', magang_views.magang_create, name='magang_create'),
    path('magang/<int:pk>/edit/', magang_views.magang_edit, name='magang_edit'),

    # Modul Absensi
    path('absensi/', absensi_views.absensi_list, name='absensi_list'),
    path('absensi/masuk/', absensi_views.absen_masuk, name='absen_masuk'),
    path('absensi/pulang/', absensi_views.absen_pulang, name='absen_pulang'),

    # Modul Kegiatan Harian & Bulanan
    path('kegiatan/', kegiatan_views.kegiatan_list, name='kegiatan_list'),
    path('kegiatan/create/', kegiatan_views.kegiatan_create, name='kegiatan_create'),
    path('kegiatan/<int:pk>/edit/', kegiatan_views.kegiatan_edit, name='kegiatan_edit'),
    path('kegiatan/<int:pk>/', kegiatan_views.kegiatan_detail, name='kegiatan_detail'),
    path('kegiatan/<int:pk>/verifikasi/', kegiatan_views.kegiatan_verifikasi, name='kegiatan_verifikasi'),
    path('rekap-bulanan/', kegiatan_views.rekap_bulanan_list, name='rekap_bulanan_list'),
    path('rekap-bulanan/generate/', kegiatan_views.generate_rekap_bulanan, name='generate_rekap_bulanan'),

    # Modul Laporan Akhir
    path('laporan/', laporan_views.laporan_detail, name='laporan_detail'),
    path('laporan/<int:pk>/', laporan_views.laporan_detail, name='laporan_detail_pk'),
    path('laporan/generate-draft/', laporan_views.laporan_generate_draft, name='laporan_generate_draft'),
    path('laporan/<int:pk>/edit/', laporan_views.laporan_edit, name='laporan_edit'),
    path('laporan/<int:pk>/status/', laporan_views.laporan_status_update, name='laporan_status_update'),
    path('laporan/<int:pk>/pdf/', laporan_views.export_pdf, name='export_pdf'),
    path('laporan/<int:pk>/word/', laporan_views.export_word, name='export_word'),

    # Export Routes
    path('export/mahasiswa/excel/', export_mahasiswa_excel, name='export_mahasiswa_excel'),
    path('export/absensi/excel/', export_absensi_excel, name='export_absensi_excel'),
    path('export/kegiatan/excel/', export_kegiatan_excel, name='export_kegiatan_excel'),
    path('export/magang/excel/', export_magang_excel, name='export_magang_excel'),
    path('export/rekap-bulanan/excel/', export_rekap_kegiatan_bulanan_excel, name='export_rekap_bulanan_excel'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
