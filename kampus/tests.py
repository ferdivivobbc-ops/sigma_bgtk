from django.core.management import call_command
from django.test import TestCase

from kampus.models import Kampus


class KampusSeedDataTest(TestCase):
    def test_seed_demo_data_creates_real_universities_and_institutes(self):
        call_command('seed_demo_data')
        kampus = Kampus.objects.filter(status='AKTIF')
        self.assertGreaterEqual(kampus.count(), 15)
        self.assertTrue(
            all(
                nama.lower().startswith(('universitas', 'institut'))
                for nama in kampus.values_list('nama_kampus', flat=True)
            )
        )
