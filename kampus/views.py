from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.decorators import admin_required
from kampus.models import Kampus

@login_required
@admin_required
def kampus_list(request):
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()

    kampus_qs = Kampus.objects.all()

    if search_query:
        kampus_qs = kampus_qs.filter(
            Q(nama_kampus__icontains=search_query) |
            Q(fakultas__icontains=search_query) |
            Q(prodi__icontains=search_query) |
            Q(alamat__icontains=search_query) |
            Q(kontak__icontains=search_query)
        )

    if status_filter:
        kampus_qs = kampus_qs.filter(status=status_filter)

    paginator = Paginator(kampus_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'kampus/kampus_list.html', context)

@login_required
@admin_required
def kampus_create(request):
    if request.method == 'POST':
        nama_kampus = request.POST.get('nama_kampus', '').strip()
        fakultas = request.POST.get('fakultas', '').strip()
        prodi = request.POST.get('prodi', '').strip()
        alamat = request.POST.get('alamat', '').strip()
        kontak = request.POST.get('kontak', '').strip()
        status = request.POST.get('status', 'AKTIF')

        if not nama_kampus:
            messages.error(request, "Nama Kampus wajib diisi.")
        else:
            Kampus.objects.create(
                nama_kampus=nama_kampus,
                fakultas=fakultas,
                prodi=prodi,
                alamat=alamat,
                kontak=kontak,
                status=status
            )
            messages.success(request, f"Kampus {nama_kampus} berhasil ditambahkan.")
            return redirect('kampus_list')

    return render(request, 'kampus/kampus_form.html', {'action': 'Tambah'})

@login_required
@admin_required
def kampus_edit(request, pk):
    kampus = get_object_or_404(Kampus, pk=pk)

    if request.method == 'POST':
        nama_kampus = request.POST.get('nama_kampus', '').strip()
        fakultas = request.POST.get('fakultas', '').strip()
        prodi = request.POST.get('prodi', '').strip()
        alamat = request.POST.get('alamat', '').strip()
        kontak = request.POST.get('kontak', '').strip()
        status = request.POST.get('status', 'AKTIF')

        if not nama_kampus:
            messages.error(request, "Nama Kampus wajib diisi.")
        else:
            kampus.nama_kampus = nama_kampus
            kampus.fakultas = fakultas
            kampus.prodi = prodi
            kampus.alamat = alamat
            kampus.kontak = kontak
            kampus.status = status
            kampus.save()
            messages.success(request, f"Data kampus {nama_kampus} berhasil diperbarui.")
            return redirect('kampus_list')

    return render(request, 'kampus/kampus_form.html', {'kampus': kampus, 'action': 'Edit'})

@login_required
@admin_required
def kampus_delete(request, pk):
    kampus = get_object_or_404(Kampus, pk=pk)
    if request.method == 'POST':
        nama = kampus.nama_kampus
        kampus.delete()
        messages.success(request, f"Kampus {nama} berhasil dihapus.")
        return redirect('kampus_list')
    return render(request, 'kampus/kampus_confirm_delete.html', {'kampus': kampus})
