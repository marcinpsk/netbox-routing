# SPDX-License-Identifier: Apache-2.0

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase

from utilities.testing import create_test_device

from netbox_routing.models import ISISInstance, Redistribution

__all__ = ('RedistributionModelTestCase',)


class RedistributionModelTestCase(TestCase):
    """Model-level (clean()) coverage for Redistribution destination scope.

    NetBox's base clean() resolves the GFK, so the destination must be a real
    object; these tests assert that a valid object of an *unsupported* type is
    still rejected by the scope check.
    """

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.isis = ISISInstance.objects.create(
            device=cls.device,
            process_tag='CORE',
            net='49.0001.0000.0000.0001.00',
            is_type='level-1-2',
        )

    def _redistribution(self, destination, **kwargs):
        return Redistribution(
            destination_type=ContentType.objects.get_for_model(type(destination)),
            destination_id=destination.pk,
            source_protocol='connected',
            **kwargs,
        )

    def test_clean_accepts_supported_destination(self):
        # ISISInstance is a valid redistribution destination scope.
        self._redistribution(self.isis).clean()  # should not raise

    def test_clean_rejects_unsupported_destination(self):
        # Device is a real object but not a valid destination scope.
        with self.assertRaises(ValidationError) as ctx:
            self._redistribution(self.device).clean()
        self.assertIn('destination_type', ctx.exception.error_dict)
