from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from accounts.models import User
from accounts.decorators import admin_required, role_required
from mahasiswa.models import Mahasiswa
from magang.models import Magang

@login_required
def magang_list(request):
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    magang_qs = Magang.objects.select_related('mahasiswa__user', 'mahasiswa__kampus', 'pembimbing').all()

    if request.user.is_pembimbing():
        magang_qs = magang_qs.filter(pembimbing=request.user)
    elif request.user.is_mahasiswa():
        magang_qs = magang_qs.filter(mahasiswa__user=request.user)

    if search_query:
        magang_qs = magang_qs.filter(
            mahasiswa__user__first_name__icontains=search_query
        ) | magang_qs.filter(bagian__icontains=search_query)

    if status_filter:
        magang_qs = magang_qs.filter(status=status_filter)

    paginator = Paginator(magang_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'magang/magang_list.html', context)

@login_required
@admin_required
def magang_create(request):
    if request.method == 'POST':
        mahasiswa_id = request.POST.get('mahasiswa', '')
        tanggal_mulai = request.POST.get('tanggal_mulai', '')
        tanggal_selesai = request.POST.get('tanggal_selesai', '')
        bagian = request.POST.get('bagian', '').strip()
        pembimbing_id = request.POST.get('pembimbing', '')
        status = request.POST.get('status', 'AKTIF')

        if not mahasiswa_id or not tanggal_mulai or not tanggal_selesai or not bagian:
            messages.error(request, "Mahasiswa, Tanggal, dan Bagian wajib diisi.")
        else:
            mahasiswa = get_object_or_404(Mahasiswa, pk=mahasiswa_id)
            Magang.objects.update_or_create(
                mahasiswa=mahasiswa,
                defaults={
                    'tanggal_mulai': tanggal_mulai,
                    'tanggal_selesai': tanggal_selesai,
                    'bagian': bagian,
                    'pembimbing_id': pembimbing_id if pembimbing_id else None,
                    'status': status
                }
            )
            messages.success(request, f"Data magang untuk {mahasiswa.user.get_full_name()} berhasil disimpan.")
            return redirect('magang_list')

    mahasiswa_available = Mahasiswa.objects.filter(status='AKTIF')
    pembimbing_list = User.objects.filter(role=User.Role.PEMBIMBING)
    return render(request, 'magang/magang_form.html', {
        'mahasiswa_list': mahasiswa_available,
        'pembimbing_list': pembimbing_list,
        'action': 'Tambah'
    })

@login_required
@admin_required
def magang_edit(request, pk):
    magang = get_object_or_404(Magang.objects.select_related('mahasiswa__user'), pk=pk)

    if request.method == 'POST':
        tanggal_mulai = request.POST.get('tanggal_mulai', '')
        tanggal_selesai = request.POST.get('tanggal_selesai', '')
        bagian = request.POST.get('bagian', '').strip()
        pembimbing_id = request.POST.get('pembimbing', '')
        status = request.POST.get('status', 'AKTIF')

        magang.tanggal_mulai = tanggal_mulai
        magang.tanggal_selesai = tanggal_selesai
        magang.bagian = bagian
        magang.pembimbing_id = pembimbing_id if pembimbing_id else None
        magang.status = status
        magang.save()

        messages.success(request, f"Data magang {magang.mahasiswa.user.get_full_name()} berhasil diperbarui.")
        return redirect('magang_list')

    pembimbing_list = User.objects.filter(role=User.Role.PEMBIMBING)
    return render(request, 'magang/magang_form.html', {
        'magang': magang,
        'pembimbing_list': pembimbing_list,
        'action': 'Edit'
    })
