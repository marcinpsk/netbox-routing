# SPDX-License-Identifier: Apache-2.0

from django.test import TestCase

from utilities.testing import create_test_device

from netbox_routing.forms import RedistributionForm
from netbox_routing.models import ISISInstance, OSPFInstance, Redistribution

__all__ = ('RedistributionFormTestCase',)


class RedistributionFormTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')
        cls.ospf = OSPFInstance.objects.create(
            name='OSPF 1', device=cls.device, router_id='1.1.1.1', process_id='1'
        )
        cls.isis = ISISInstance.objects.create(
            device=cls.device,
            process_tag='CORE',
            net='49.0001.0000.0000.0001.00',
            is_type='level-1-2',
        )

    def test_redistribution_valid(self):
        form = RedistributionForm(
            data={
                'ospf_instance': self.ospf.pk,
                'source_protocol': 'connected',
                'metric': 5,
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.destination, self.ospf)

    def test_redistribution_requires_destination(self):
        # No destination selector chosen -> the form must reject the submission.
        form = RedistributionForm(data={'source_protocol': 'connected'})
        self.assertFalse(form.is_valid())

    def test_redistribution_single_destination_only(self):
        # Selecting two destination scopes at once is rejected.
        form = RedistributionForm(
            data={
                'ospf_instance': self.ospf.pk,
                'isis_instance': self.isis.pk,
                'source_protocol': 'connected',
            }
        )
        self.assertFalse(form.is_valid())

    def test_redistribution_metric_type_scope(self):
        # An IS-IS metric type on an OSPF destination is rejected by clean().
        form = RedistributionForm(
            data={
                'ospf_instance': self.ospf.pk,
                'source_protocol': 'connected',
                'metric_type': 'internal',
            }
        )
        self.assertFalse(form.is_valid())
        self.assertEqual(Redistribution.objects.count(), 0)
