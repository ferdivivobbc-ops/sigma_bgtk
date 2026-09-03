from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.is_superuser or request.user.role in allowed_roles:
                if 'MAHASISWA' in allowed_roles and request.user.role == 'MAHASISWA':
                    if getattr(request.user, 'mahasiswa_profile', None) is None:
                        messages.error(request, "Profil mahasiswa belum dikonfigurasi. Hubungi admin untuk melanjutkan.")
                        return redirect('dashboard')
                return view_func(request, *args, **kwargs)
            messages.error(request, "Anda tidak memiliki akses ke halaman tersebut.")
            return redirect('dashboard')
        return _wrapped_view
    return decorator

def admin_required(view_func):
    return role_required('ADMIN')(view_func)

def pembimbing_required(view_func):
    return role_required('PEMBIMBING', 'ADMIN')(view_func)

def mahasiswa_required(view_func):
    return role_required('MAHASISWA')(view_func)
