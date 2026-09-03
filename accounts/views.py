from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.db import IntegrityError, transaction
from django.views.decorators.http import require_POST
from datetime import date, datetime
import json
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from accounts.models import User, Notification, AuditLog
from kampus.models import Kampus
from mahasiswa.models import Mahasiswa
from magang.models import Magang
from absensi.models import Absensi
from kegiatan.models import KegiatanHarian, KegiatanBulanan
from laporan.models import LaporanAkhir
from accounts.decorators import admin_required


@login_required
@admin_required
def pembimbing_list(request):
    pembimbing_users = User.objects.filter(role=User.Role.PEMBIMBING).order_by('first_name', 'last_name')
    return render(request, 'accounts/pembimbing_list.html', {'pembimbing_list': pembimbing_users})


@login_required
@admin_required
def pembimbing_create(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip().lower()
        full_name = request.POST.get('full_name', '').strip()
        no_hp = request.POST.get('no_hp', '').strip()
        password = request.POST.get('password', '').strip()

        if not username or not email or not full_name or not password:
            messages.error(request, 'Username, email, nama, dan password wajib diisi.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username tersebut sudah digunakan.')
        elif User.objects.filter(email__iexact=email).exists():
            messages.error(request, 'Email tersebut sudah digunakan.')
        else:
            try:
                with transaction.atomic():
                    User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                        first_name=full_name,
                        no_hp=no_hp,
                        role=User.Role.PEMBIMBING,
                    )
            except IntegrityError:
                messages.error(request, 'Akun pembimbing gagal dibuat karena username atau email sudah terdaftar.')
            else:
                messages.success(request, f'Akun pembimbing {full_name} berhasil dibuat.')
                return redirect('pembimbing_list')

    return render(request, 'accounts/pembimbing_form.html')


@login_required
@admin_required
@require_POST
def pembimbing_delete(request, pk):
    pembimbing = get_object_or_404(User, pk=pk, role=User.Role.PEMBIMBING)
    name = pembimbing.get_full_name() or pembimbing.username
    pembimbing.delete()
    messages.success(request, f'Akun pembimbing {name} berhasil dihapus.')
    return redirect('pembimbing_list')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        email_or_username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=email_or_username, password=password)
        if user is None:
            # Fallback try matching by email
            try:
                user_obj = User.objects.get(email=email_or_username)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is not None:
            login(request, user)
            messages.success(request, f"Selamat datang kembali, {user.get_full_name() or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Username/Email atau password salah.")

    return render(request, 'accounts/login.html')


def google_login_view(request):
    from django.conf import settings

    if request.user.is_authenticated:
        return redirect('dashboard')
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.error(request, 'Login Google belum dikonfigurasi oleh administrator.')
        return redirect('login')

    state = secrets.token_urlsafe(32)
    request.session['google_oauth_state'] = state
    params = urlencode({
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
    })
    return redirect(f'https://accounts.google.com/o/oauth2/v2/auth?{params}')


def google_callback_view(request):
    from django.conf import settings

    if request.GET.get('state') != request.session.pop('google_oauth_state', None):
        messages.error(request, 'Sesi login Google tidak valid. Silakan coba lagi.')
        return redirect('login')
    if request.GET.get('error'):
        messages.error(request, 'Login Google dibatalkan.')
        return redirect('login')
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        messages.error(request, 'Login Google belum dikonfigurasi oleh administrator.')
        return redirect('login')

    try:
        token_request = Request(
            'https://oauth2.googleapis.com/token',
            data=urlencode({
                'code': request.GET.get('code', ''),
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                'grant_type': 'authorization_code',
            }).encode(),
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST',
        )
        with urlopen(token_request, timeout=10) as response:
            token_data = json.loads(response.read().decode())
        access_token = token_data.get('access_token')
        if not access_token:
            raise ValueError('Token Google tidak ditemukan.')

        userinfo_request = Request(
            'https://openidconnect.googleapis.com/v1/userinfo',
            headers={'Authorization': f'Bearer {access_token}'},
        )
        with urlopen(userinfo_request, timeout=10) as response:
            google_user = json.loads(response.read().decode())
    except (HTTPError, URLError, ValueError, json.JSONDecodeError):
        messages.error(request, 'Google tidak dapat memverifikasi akun tersebut.')
        return redirect('login')

    email = google_user.get('email', '').strip().lower()
    if not email or not google_user.get('email_verified'):
        messages.error(request, 'Email Google belum terverifikasi.')
        return redirect('login')

    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None:
        messages.error(request, 'Email Google belum terdaftar sebagai akun SIGMA. Hubungi Admin.')
        return redirect('login')

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, f'Selamat datang, {user.get_full_name() or user.username}!')
    return redirect('dashboard')

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "Anda telah keluar dari sistem.")
    return redirect('login')

@login_required
def dashboard_view(request):
    user = request.user
    today = date.today()

    if user.is_admin():
        # Admin Dashboard context
        total_mahasiswa_aktif = Mahasiswa.objects.filter(status='AKTIF').count()
        total_pembimbing = User.objects.filter(role=User.Role.PEMBIMBING).count()
        total_kampus = Kampus.objects.filter(status='AKTIF').count()
        total_magang_aktif = Magang.objects.filter(status='AKTIF').count()
        total_magang_selesai = Magang.objects.filter(status='SELESAI').count()
        hadir_hari_ini = Absensi.objects.filter(tanggal=today, status='HADIR').count()
        kegiatan_unverified = KegiatanHarian.objects.filter(status_verifikasi='MENUNGGU').count()

        # Campus breakdown chart data
        kampus_chart = Kampus.objects.annotate(
            total_mhs=Count('mahasiswa_list', filter=Q(mahasiswa_list__status='AKTIF'))
        ).values('nama_kampus', 'total_mhs')

        # Recent activities
        recent_activities = KegiatanHarian.objects.select_related('mahasiswa__user').order_by('-created_at')[:5]

        context = {
            'role': 'ADMIN',
            'total_mahasiswa_aktif': total_mahasiswa_aktif,
            'total_pembimbing': total_pembimbing,
            'total_kampus': total_kampus,
            'total_magang_aktif': total_magang_aktif,
            'total_magang_selesai': total_magang_selesai,
            'hadir_hari_ini': hadir_hari_ini,
            'kegiatan_unverified': kegiatan_unverified,
            'kampus_chart': list(kampus_chart),
            'recent_activities': recent_activities,
            'today': today,
        }
        return render(request, 'dashboard/admin.html', context)

    elif user.is_pembimbing():
        # Pembimbing Dashboard context
        bimbingan_list = Magang.objects.filter(pembimbing=user, status='AKTIF').select_related('mahasiswa__user', 'mahasiswa__kampus')
        mahasiswa_ids = bimbingan_list.values_list('mahasiswa_id', flat=True)

        total_bimbingan = len(bimbingan_list)
        hadir_hari_ini = Absensi.objects.filter(mahasiswa_id__in=mahasiswa_ids, tanggal=today, status='HADIR').count()
        unverified_kegiatan = KegiatanHarian.objects.filter(mahasiswa_id__in=mahasiswa_ids, status_verifikasi='MENUNGGU').count()
        verified_kegiatan = KegiatanHarian.objects.filter(mahasiswa_id__in=mahasiswa_ids, status_verifikasi='DISETUJUI').count()
        pending_laporan = LaporanAkhir.objects.filter(mahasiswa_id__in=mahasiswa_ids, status='PERIKSA').count()

        context = {
            'role': 'PEMBIMBING',
            'total_bimbingan': total_bimbingan,
            'hadir_hari_ini': hadir_hari_ini,
            'unverified_kegiatan': unverified_kegiatan,
            'verified_kegiatan': verified_kegiatan,
            'pending_laporan': pending_laporan,
            'bimbingan_list': bimbingan_list,
        }
        return render(request, 'dashboard/pembimbing.html', context)

    else:
        # Mahasiswa Dashboard context
        try:
            mhs = request.user.mahasiswa_profile
        except Mahasiswa.DoesNotExist:
            messages.warning(request, "Profil mahasiswa belum dikonfigurasi. Menghubungi Admin.")
            return render(request, 'dashboard/mahasiswa.html', {'role': 'MAHASISWA', 'no_profile': True})

        magang_info = getattr(mhs, 'data_magang', None)
        total_kehadiran = Absensi.objects.filter(mahasiswa=mhs, status='HADIR').count()
        total_kegiatan = KegiatanHarian.objects.filter(mahasiswa=mhs).count()
        kegiatan_unverified = KegiatanHarian.objects.filter(mahasiswa=mhs, status_verifikasi='MENUNGGU').count()
        kegiatan_approved = KegiatanHarian.objects.filter(mahasiswa=mhs, status_verifikasi='DISETUJUI').count()

        # Check today's attendance status
        absensi_today = Absensi.objects.filter(mahasiswa=mhs, tanggal=today).order_by('-jam_masuk').first()

        # Calculate attendance percentage based on active magang days
        attendance_percentage = 100
        if magang_info and magang_info.tanggal_mulai:
            days_elapsed = max(1, (today - magang_info.tanggal_mulai).days + 1)
            attendance_percentage = min(100, int((total_kehadiran / days_elapsed) * 100))

        context = {
            'role': 'MAHASISWA',
            'mahasiswa': mhs,
            'magang_info': magang_info,
            'total_kehadiran': total_kehadiran,
            'total_kegiatan': total_kegiatan,
            'kegiatan_unverified': kegiatan_unverified,
            'kegiatan_approved': kegiatan_approved,
            'attendance_percentage': attendance_percentage,
            'absensi_today': absensi_today,
            'today': today,
        }
        return render(request, 'dashboard/mahasiswa.html', context)

@login_required
def profile_view(request):
    user = request.user
    mahasiswa = getattr(user, 'mahasiswa_profile', None)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        no_hp = request.POST.get('no_hp', '').strip()

        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.no_hp = no_hp
        user.save()

        if mahasiswa:
            prodi = request.POST.get('prodi', '').strip()
            mahasiswa.prodi = prodi
            if 'foto' in request.FILES:
                foto = request.FILES['foto']
                extension = foto.name.rsplit('.', 1)[-1].lower() if '.' in foto.name else ''
                if extension not in {'jpg', 'jpeg', 'png', 'webp'} or foto.size > 5 * 1024 * 1024:
                    messages.error(request, "Foto profil harus JPG, PNG, atau WEBP dan maksimal 5 MB.")
                    return render(request, 'accounts/profile.html', {'user': user, 'mahasiswa': mahasiswa})
                mahasiswa.foto = foto
            mahasiswa.save()

        AuditLog.objects.create(actor=user, action='UPDATE', model_name='Profile', object_id=user.pk, description='Memperbarui profil pengguna')
        messages.success(request, "Profil berhasil diperbarui.")
        return redirect('profile')

    return render(request, 'accounts/profile.html', {'user': user, 'mahasiswa': mahasiswa})


@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user)
    return render(request, 'accounts/notifications.html', {'notifications': notifications})


@login_required
def notification_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=['is_read'])
    return redirect(notification.link or 'notifications')


@login_required
def notifications_mark_all_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'Semua notifikasi ditandai sudah dibaca.')
    return redirect('notifications')


@login_required
def password_change_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        if not request.user.check_password(current_password):
            messages.error(request, 'Password saat ini tidak sesuai.')
        elif len(new_password) < 8:
            messages.error(request, 'Password baru minimal 8 karakter.')
        elif new_password != confirm_password:
            messages.error(request, 'Konfirmasi password baru tidak sama.')
        else:
            request.user.set_password(new_password)
            request.user.save(update_fields=['password'])
            update_session_auth_hash(request, request.user)
            AuditLog.objects.create(actor=request.user, action='UPDATE', model_name='Password', object_id=request.user.pk, description='Mengganti password')
            messages.success(request, 'Password berhasil diubah.')
            return redirect('profile')
    return render(request, 'accounts/password_change.html')


@login_required
def audit_log_view(request):
    if not request.user.is_admin():
        messages.error(request, 'Hanya admin yang dapat melihat audit log.')
        return redirect('dashboard')
    logs = AuditLog.objects.select_related('actor')[:200]
    return render(request, 'accounts/audit_log.html', {'audit_logs': logs})
