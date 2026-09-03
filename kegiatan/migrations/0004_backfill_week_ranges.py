from datetime import timedelta

from django.db import migrations


def backfill_week_ranges(apps, schema_editor):
    KegiatanHarian = apps.get_model('kegiatan', 'KegiatanHarian')
    for kegiatan in KegiatanHarian.objects.filter(minggu_mulai__isnull=True):
        minggu_mulai = kegiatan.tanggal - timedelta(days=kegiatan.tanggal.weekday())
        kegiatan.minggu_mulai = minggu_mulai
        kegiatan.minggu_selesai = minggu_mulai + timedelta(days=6)
        kegiatan.save(update_fields=['minggu_mulai', 'minggu_selesai'])


class Migration(migrations.Migration):
    dependencies = [('kegiatan', '0003_alter_kegiatanharian_options')]

    operations = [migrations.RunPython(backfill_week_ranges, migrations.RunPython.noop)]