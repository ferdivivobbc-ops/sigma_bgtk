from datetime import date, datetime, time
from decimal import Decimal

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db.models.fields.files import FieldFile

from utils.firebase import get_firestore_client


CUSTOM_APP_LABELS = {
    "accounts",
    "kampus",
    "mahasiswa",
    "magang",
    "absensi",
    "kegiatan",
    "laporan",
}


def serialize_value(value):
    if isinstance(value, FieldFile):
        return value.name or None
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def serialize_instance(instance):
    document = {"django_pk": str(instance.pk)}
    for field in instance._meta.concrete_fields:
        if field.name == "id":
            continue
        value = getattr(instance, field.attname)
        document[field.attname] = serialize_value(value)
    return document


class Command(BaseCommand):
    help = "Copy Django model data from SQLite/PostgreSQL into Firestore."

    def add_arguments(self, parser):
        parser.add_argument(
            "--app",
            dest="app_label",
            help="Only migrate one application label.",
        )
        parser.add_argument(
            "--include-auth",
            action="store_true",
            help="Also copy Django auth/contenttypes data.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Count records without connecting to Firestore or writing data.",
        )

    def handle(self, *args, **options):
        app_label = options.get("app_label")
        include_auth = options["include_auth"]
        dry_run = options["dry_run"]

        allowed_apps = set(CUSTOM_APP_LABELS)
        if include_auth:
            allowed_apps.update({"auth", "contenttypes"})
        if app_label:
            if app_label not in allowed_apps:
                raise CommandError(f"Aplikasi tidak dikenal atau tidak diizinkan: {app_label}")
            allowed_apps = {app_label}

        models = [
            model
            for model in apps.get_models()
            if model._meta.app_label in allowed_apps
        ]
        if not models:
            raise CommandError("Tidak ada model yang cocok untuk dimigrasikan.")

        client = None if dry_run else get_firestore_client()
        total = 0
        for model in models:
            collection_name = f"{model._meta.app_label}_{model._meta.model_name}"
            count = model.objects.count()
            total += count
            self.stdout.write(f"{collection_name}: {count} dokumen")
            if dry_run:
                continue

            batch = client.batch()
            pending = 0
            for instance in model.objects.iterator():
                reference = client.collection(collection_name).document(str(instance.pk))
                batch.set(reference, serialize_instance(instance))
                pending += 1
                if pending >= 400:
                    batch.commit()
                    batch = client.batch()
                    pending = 0
            if pending:
                batch.commit()

        action = "diperkirakan" if dry_run else "berhasil disalin"
        self.stdout.write(self.style.SUCCESS(f"Total {total} record {action} ke Firestore."))
