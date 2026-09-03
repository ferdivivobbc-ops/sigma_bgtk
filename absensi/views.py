from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import date, time

from accounts.decorators import mahasiswa_required, role_required
from mahasiswa.models import Mahasiswa
from absensi.models import Absensi


ABSEN_MASUK_MULAI = time(7, 30)
ABSEN_MASUK_SELESAI = time(16, 0)


def _valid_attendance_photo(photo):
    if not photo:
        return False
    extension = photo.name.rsplit('.', 1)[-1].lower() if '.' in photo.name else ''
    return extension in {'jpg', 'jpeg', 'png', 'webp'} and photo.size <= 5 * 1024 * 1024

@login_required
@mahasiswa_required
def absen_masuk(request):
    mhs = request.user.mahasiswa_profile
    today = date.today()

    # Check if student already checked in today
    absensi_today = Absensi.objects.filter(mahasiswa=mhs, tanggal=today).first()
    if absensi_today:
        messages.warning(request, "Anda sudah melakukan absensi masuk hari ini.")
        return redirect('dashboard')

    if request.method == 'POST':
        status = request.POST.get('status', 'HADIR')
        latitude = request.POST.get('latitude', '')
        longitude = request.POST.get('longitude', '')
        now_time = timezone.localtime().time()
        foto = request.FILES.get('foto')

        if not ABSEN_MASUK_MULAI <= now_time <= ABSEN_MASUK_SELESAI:
            messages.error(
                request,
                'Absensi masuk hanya tersedia setiap hari pukul 07:30 sampai 16:00.'
            )
            return render(
                request,
                'absensi/absen_masuk.html',
                {'today': today, 'mahasiswa': mhs}
            )

        if not _valid_attendance_photo(foto):
            messages.error(request, "Foto absensi wajib berupa JPG, PNG, atau WEBP dengan ukuran maksimal 5 MB.")
            return render(request, 'absensi/absen_masuk.html', {'today': today, 'mahasiswa': mhs})

        absensi = Absensi(
            mahasiswa=mhs,
            tanggal=today,
            jam_masuk=now_time,
            status=status,
            latitude=latitude,
            longitude=longitude,
            foto_masuk=foto
        )

        try:
            absensi.save()
            messages.success(request, f"Absensi masuk berhasil dicatat pada jam {now_time.strftime('%H:%M:%S')}.")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan saat menyimpan absensi: {e}")

    return render(request, 'absensi/absen_masuk.html', {'today': today, 'mahasiswa': mhs})

@login_required
@mahasiswa_required
def absen_pulang(request):
    mhs = request.user.mahasiswa_profile
    today = date.today()

    absensi_today = Absensi.objects.filter(mahasiswa=mhs, tanggal=today).order_by('-jam_masuk').first()
    if not absensi_today or absensi_today.jam_masuk is None:
        messages.error(request, "Anda belum melakukan absensi masuk hari ini.")
        return redirect('absen_masuk')

    if absensi_today.jam_pulang is not None:
        messages.info(request, "Anda sudah melakukan absensi pulang hari ini.")
        return redirect('dashboard')

    if request.method == 'POST':
        now_time = timezone.localtime().time()
        foto = request.FILES.get('foto')

        if not _valid_attendance_photo(foto):
            messages.error(request, "Foto absensi pulang wajib berupa JPG, PNG, atau WEBP dengan ukuran maksimal 5 MB.")
            return render(request, 'absensi/absen_pulang.html', {'absensi': absensi_today, 'today': today})

        absensi_today.jam_pulang = now_time
        absensi_today.foto_pulang = foto
        absensi_today.save()

        messages.success(request, f"Absensi pulang berhasil dicatat pada jam {now_time.strftime('%H:%M:%S')}.")
        return redirect('dashboard')

    return render(request, 'absensi/absen_pulang.html', {'absensi': absensi_today, 'today': today})

@login_required
@role_required('ADMIN', 'PEMBIMBING')
def absensi_list(request):
    user = request.user
    search_query = request.GET.get('q', '').strip()
    month_filter = request.GET.get('bulan', '').strip()
    year_filter = request.GET.get('tahun', '').strip()
    status_filter = request.GET.get('status', '').strip()

    absensi_qs = Absensi.objects.select_related('mahasiswa__user', 'mahasiswa__kampus').all()

    if user.is_pembimbing():
        absensi_qs = absensi_qs.filter(mahasiswa__data_magang__pembimbing=user)

    if search_query:
        absensi_qs = absensi_qs.filter(
            Q(mahasiswa__user__first_name__icontains=search_query) |
            Q(mahasiswa__nim__icontains=search_query)
        )

    if month_filter:
        absensi_qs = absensi_qs.filter(tanggal__month=int(month_filter))

    if year_filter:
        absensi_qs = absensi_qs.filter(tanggal__year=int(year_filter))

    if status_filter:
        absensi_qs = absensi_qs.filter(status=status_filter)

    paginator = Paginator(absensi_qs, 15)
    page_obj = paginator.get_page(request.GET.get('page'))

    months = range(1, 13)
    years = range(2025, 2028)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'month_filter': month_filter,
        'year_filter': year_filter,
        'status_filter': status_filter,
        'months': months,
        'years': years,
    }
    return render(request, 'absensi/absensi_list.html', context)
