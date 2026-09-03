from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import date, datetime, timedelta

from accounts.decorators import mahasiswa_required, pembimbing_required, role_required
from mahasiswa.models import Mahasiswa
from absensi.models import Absensi
from kegiatan.models import KegiatanHarian, KegiatanBulanan
from utils.email_notifier import send_kegiatan_status_notification
from accounts.models import Notification, AuditLog


def _week_range(value):
    selected = datetime.strptime(value, '%Y-%m-%d').date()
    start = selected - timedelta(days=selected.weekday())
    return start, start + timedelta(days=6)

@login_required
def kegiatan_list(request):
    user = request.user
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    month_filter = request.GET.get('bulan', '').strip()
    week_filter = request.GET.get('minggu', '').strip()

    kegiatan_qs = KegiatanHarian.objects.select_related('mahasiswa__user', 'mahasiswa__kampus').all()

    if user.is_mahasiswa():
        mhs = user.mahasiswa_profile
        kegiatan_qs = kegiatan_qs.filter(mahasiswa=mhs)
    elif user.is_pembimbing():
        kegiatan_qs = kegiatan_qs.filter(mahasiswa__data_magang__pembimbing=user)

    if search_query:
        kegiatan_qs = kegiatan_qs.filter(
            Q(judul_kegiatan__icontains=search_query) |
            Q(kegiatan__icontains=search_query) |
            Q(mahasiswa__user__first_name__icontains=search_query)
        )

    if status_filter:
        kegiatan_qs = kegiatan_qs.filter(status_verifikasi=status_filter)

    if month_filter:
        kegiatan_qs = kegiatan_qs.filter(tanggal__month=int(month_filter))

    if week_filter:
        week_start, week_end = _week_range(week_filter)
        kegiatan_qs = kegiatan_qs.filter(
            tanggal__gte=week_start,
            tanggal__lte=week_end,
        )

    paginator = Paginator(kegiatan_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'month_filter': month_filter,
        'week_filter': week_filter,
        'months': range(1, 13),
    }
    return render(request, 'kegiatan/kegiatan_list.html', context)

@login_required
@mahasiswa_required
def kegiatan_create(request):
    mhs = getattr(request.user, 'mahasiswa_profile', None)
    if mhs is None:
        messages.error(request, "Profil mahasiswa belum dikonfigurasi. Hubungi admin untuk melanjutkan.")
        return redirect('dashboard')

    if request.method == 'POST':
        tanggal = request.POST.get('tanggal', str(date.today()))
        minggu_mulai = request.POST.get('minggu_mulai', tanggal)
        judul_kegiatan = request.POST.get('judul_kegiatan', '').strip()
        kegiatan = request.POST.get('kegiatan', '').strip()
        hasil = request.POST.get('hasil', '').strip()
        kendala = request.POST.get('kendala', 'Tidak ada kendala').strip()
        solusi = request.POST.get('solusi', 'Tidak ada').strip()

        try:
            minggu_mulai_date, minggu_selesai_date = _week_range(minggu_mulai)
            tanggal_date = datetime.strptime(tanggal, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            messages.error(request, "Tanggal kegiatan atau periode minggu tidak valid.")
            return render(request, 'kegiatan/kegiatan_form.html', {'today': date.today()})

        if not judul_kegiatan or not kegiatan or not hasil:
            messages.error(request, "Judul kegiatan, Uraian kegiatan, dan Hasil kegiatan wajib diisi.")
        else:
            dokumentasi = request.FILES.get('dokumentasi')
            if dokumentasi:
                extension = dokumentasi.name.rsplit('.', 1)[-1].lower() if '.' in dokumentasi.name else ''
                if extension not in {'jpg', 'jpeg', 'png', 'webp'} or dokumentasi.size > 5 * 1024 * 1024:
                    messages.error(request, "Dokumentasi harus berupa JPG, PNG, atau WEBP dan maksimal 5 MB.")
                    return render(request, 'kegiatan/kegiatan_form.html', {'today': date.today()})
            obj = KegiatanHarian(
                mahasiswa=mhs,
                tanggal=tanggal_date,
                minggu_mulai=minggu_mulai_date,
                minggu_selesai=minggu_selesai_date,
                judul_kegiatan=judul_kegiatan,
                kegiatan=kegiatan,
                hasil=hasil,
                kendala=kendala,
                solusi=solusi,
                status_verifikasi='MENUNGGU'
            )
            if dokumentasi:
                obj.dokumentasi = dokumentasi
            obj.save()

            AuditLog.objects.create(actor=request.user, action='CREATE', model_name='KegiatanMingguan', object_id=obj.pk, description=obj.judul_kegiatan)
            magang = getattr(mhs, 'data_magang', None)
            if magang and magang.pembimbing_id:
                Notification.objects.create(
                    recipient=magang.pembimbing,
                    title='Kegiatan mingguan baru',
                    message=f'{mhs.user.get_full_name()} mengirim kegiatan "{obj.judul_kegiatan}" untuk diverifikasi.',
                    link=f'/kegiatan/{obj.pk}/',
                )

            messages.success(request, "Kegiatan mingguan berhasil disimpan dan menunggu verifikasi pembimbing.")
            return redirect('kegiatan_list')

    return render(request, 'kegiatan/kegiatan_form.html', {'today': date.today()})


@login_required
@mahasiswa_required
def kegiatan_edit(request, pk):
    kegiatan_obj = get_object_or_404(KegiatanHarian, pk=pk, mahasiswa=request.user.mahasiswa_profile)
    if kegiatan_obj.status_verifikasi not in {'MENUNGGU', 'PERLU_REVISI'}:
        messages.error(request, "Kegiatan yang sudah disetujui atau ditolak tidak dapat diedit.")
        return redirect('kegiatan_detail', pk=pk)

    if request.method == 'POST':
        tanggal = request.POST.get('tanggal', str(kegiatan_obj.tanggal))
        minggu_mulai = request.POST.get('minggu_mulai', tanggal)
        try:
            tanggal_date = datetime.strptime(tanggal, '%Y-%m-%d').date()
            minggu_mulai_date, minggu_selesai_date = _week_range(minggu_mulai)
        except (TypeError, ValueError):
            messages.error(request, "Tanggal kegiatan atau periode minggu tidak valid.")
            return render(request, 'kegiatan/kegiatan_form.html', {'today': date.today(), 'kegiatan': kegiatan_obj})

        dokumentasi = request.FILES.get('dokumentasi')
        if dokumentasi:
            extension = dokumentasi.name.rsplit('.', 1)[-1].lower() if '.' in dokumentasi.name else ''
            if extension not in {'jpg', 'jpeg', 'png', 'webp'} or dokumentasi.size > 5 * 1024 * 1024:
                messages.error(request, "Dokumentasi harus berupa JPG, PNG, atau WEBP dan maksimal 5 MB.")
                return render(request, 'kegiatan/kegiatan_form.html', {'today': date.today(), 'kegiatan': kegiatan_obj})

        kegiatan_obj.tanggal = tanggal_date
        kegiatan_obj.minggu_mulai = minggu_mulai_date
        kegiatan_obj.minggu_selesai = minggu_selesai_date
        kegiatan_obj.judul_kegiatan = request.POST.get('judul_kegiatan', '').strip()
        kegiatan_obj.kegiatan = request.POST.get('kegiatan', '').strip()
        kegiatan_obj.hasil = request.POST.get('hasil', '').strip()
        kegiatan_obj.kendala = request.POST.get('kendala', 'Tidak ada kendala').strip()
        kegiatan_obj.solusi = request.POST.get('solusi', 'Tidak ada').strip()
        kegiatan_obj.status_verifikasi = 'MENUNGGU'
        kegiatan_obj.komentar_pembimbing = ''
        kegiatan_obj.verified_by = None
        kegiatan_obj.verified_at = None
        if dokumentasi:
            kegiatan_obj.dokumentasi = dokumentasi
        kegiatan_obj.save()

        AuditLog.objects.create(actor=request.user, action='UPDATE', model_name='KegiatanMingguan', object_id=pk, description='Mahasiswa memperbarui kegiatan')
        magang = getattr(kegiatan_obj.mahasiswa, 'data_magang', None)
        if magang and magang.pembimbing_id:
            Notification.objects.create(
                recipient=magang.pembimbing,
                title='Kegiatan mingguan diperbarui',
                message=f'{request.user.get_full_name()} memperbarui kegiatan "{kegiatan_obj.judul_kegiatan}".',
                link=f'/kegiatan/{pk}/',
            )
        messages.success(request, "Kegiatan mingguan berhasil diperbarui dan dikirim ulang untuk verifikasi.")
        return redirect('kegiatan_detail', pk=pk)

    return render(request, 'kegiatan/kegiatan_form.html', {'today': date.today(), 'kegiatan': kegiatan_obj})

@login_required
def kegiatan_detail(request, pk):
    kegiatan_obj = get_object_or_404(KegiatanHarian.objects.select_related('mahasiswa__user', 'verified_by'), pk=pk)
    if request.user.is_mahasiswa() and kegiatan_obj.mahasiswa.user_id != request.user.id:
        messages.error(request, "Anda tidak memiliki akses ke kegiatan tersebut.")
        return redirect('kegiatan_list')
    magang = getattr(kegiatan_obj.mahasiswa, 'data_magang', None)
    if request.user.is_pembimbing() and (not magang or magang.pembimbing_id != request.user.id):
        messages.error(request, "Kegiatan ini bukan dari mahasiswa bimbingan Anda.")
        return redirect('kegiatan_list')
    return render(request, 'kegiatan/kegiatan_detail.html', {'kegiatan': kegiatan_obj})

@login_required
@pembimbing_required
def kegiatan_verifikasi(request, pk):
    kegiatan_obj = get_object_or_404(KegiatanHarian.objects.select_related('mahasiswa__user'), pk=pk)
    magang = getattr(kegiatan_obj.mahasiswa, 'data_magang', None)
    if request.user.is_pembimbing() and (not magang or magang.pembimbing_id != request.user.id):
        messages.error(request, "Kegiatan ini bukan dari mahasiswa bimbingan Anda.")
        return redirect('kegiatan_list')

    if request.method == 'POST':
        status = request.POST.get('status_verifikasi', 'DISETUJUI')
        komentar = request.POST.get('komentar_pembimbing', '').strip()

        kegiatan_obj.status_verifikasi = status
        kegiatan_obj.komentar_pembimbing = komentar
        kegiatan_obj.verified_by = request.user
        kegiatan_obj.verified_at = timezone.now()
        kegiatan_obj.save()
        status_display = kegiatan_obj.get_status_verifikasi_display()
        AuditLog.objects.create(actor=request.user, action='VERIFY', model_name='KegiatanMingguan', object_id=kegiatan_obj.pk, description=status)
        Notification.objects.create(
            recipient=kegiatan_obj.mahasiswa.user,
            title='Status kegiatan diperbarui',
            message=f'Kegiatan "{kegiatan_obj.judul_kegiatan}" berstatus {status_display}.',
            link=f'/kegiatan/{kegiatan_obj.pk}/',
        )

        # Send email notification to mahasiswa
        try:
            send_kegiatan_status_notification(
                kegiatan_obj.mahasiswa,
                kegiatan_obj,
                status
            )
        except Exception as e:
            print(f"Error sending email: {str(e)}")
        
        messages.success(request, f"Status kegiatan berhasil diubah menjadi '{status_display}'.")
        return redirect('kegiatan_list')

    return render(request, 'kegiatan/kegiatan_verifikasi.html', {'kegiatan': kegiatan_obj})

@login_required
def rekap_bulanan_list(request):
    user = request.user
    search_query = request.GET.get('q', '').strip()
    month_filter = request.GET.get('bulan', '').strip()
    year_filter = request.GET.get('tahun', str(date.today().year))

    rekap_qs = KegiatanBulanan.objects.select_related('mahasiswa__user', 'mahasiswa__kampus').all()

    if user.is_mahasiswa():
        mhs = user.mahasiswa_profile
        rekap_qs = rekap_qs.filter(mahasiswa=mhs)
    elif user.is_pembimbing():
        rekap_qs = rekap_qs.filter(mahasiswa__data_magang__pembimbing=user)

    if search_query:
        rekap_qs = rekap_qs.filter(mahasiswa__user__first_name__icontains=search_query)

    if month_filter:
        rekap_qs = rekap_qs.filter(bulan=int(month_filter))

    if year_filter:
        rekap_qs = rekap_qs.filter(tahun=int(year_filter))

    context = {
        'rekap_list': rekap_qs,
        'search_query': search_query,
        'month_filter': month_filter,
        'year_filter': year_filter,
        'months': range(1, 13),
        'years': range(2025, 2028),
    }
    return render(request, 'kegiatan/rekap_bulanan_list.html', context)

@login_required
def generate_rekap_bulanan(request):
    if request.method == 'POST':
        bulan = int(request.POST.get('bulan', date.today().month))
        tahun = int(request.POST.get('tahun', date.today().year))

        if request.user.is_mahasiswa():
            mhs_list = [request.user.mahasiswa_profile]
        else:
            mhs_list = Mahasiswa.objects.filter(status='AKTIF')

        generated_count = 0
        for mhs in mhs_list:
            total_hadir = Absensi.objects.filter(
                mahasiswa=mhs,
                tanggal__month=bulan,
                tanggal__year=tahun,
                status='HADIR'
            ).count()

            kegiatan_qs = KegiatanHarian.objects.filter(
                mahasiswa=mhs,
                tanggal__month=bulan,
                tanggal__year=tahun
            )
            total_kegiatan = kegiatan_qs.count()
            total_disetujui = kegiatan_qs.filter(status_verifikasi='DISETUJUI').count()

            # Compile ringkasan activities
            judul_list = kegiatan_qs.values_list('judul_kegiatan', flat=True)[:5]
            summary_text = f"Rekapitulasi kegiatan bulan {bulan}/{tahun}. Total Kehadiran: {total_hadir} hari. Total Kegiatan: {total_kegiatan} ({total_disetujui} disetujui)."
            if judul_list:
                summary_text += " Kegiatan utama: " + ", ".join(judul_list) + "."

            KegiatanBulanan.objects.update_or_create(
                mahasiswa=mhs,
                bulan=bulan,
                tahun=tahun,
                defaults={
                    'ringkasan': summary_text,
                    'total_hadir': total_hadir,
                    'total_kegiatan': total_kegiatan,
                    'total_disetujui': total_disetujui,
                }
            )
            generated_count += 1

        messages.success(request, f"Berhasil membuat/memperbarui rekap bulanan ({bulan}/{tahun}) untuk {generated_count} mahasiswa.")
        return redirect('rekap_bulanan_list')

    return redirect('rekap_bulanan_list')
