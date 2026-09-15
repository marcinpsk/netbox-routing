# SPDX-License-Identifier: Apache-2.0

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from utilities.testing import create_test_device

from netbox_routing.filtersets import RedistributionFilterSet
from netbox_routing.models import (
    ISISInstance,
    OSPFInstance,
    Redistribution,
    RouteMap,
)

__all__ = ('RedistributionFilterSetTestCase',)


class RedistributionFilterSetTestCase(TestCase):
    queryset = Redistribution.objects.all()
    filterset = RedistributionFilterSet

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
        ospf = OSPFInstance.objects.create(
            name='OSPF 1', device=device, router_id='1.1.1.1', process_id='1'
        )
        isis = ISISInstance.objects.create(
            device=device,
            process_tag='CORE',
            net='49.0001.0000.0000.0001.00',
            is_type='level-1-2',
        )
        cls.route_map = RouteMap.objects.create(name='RM 1')
        ospf_ct = ContentType.objects.get_for_model(OSPFInstance)
        isis_ct = ContentType.objects.get_for_model(ISISInstance)

        redistributions = (
            Redistribution(
                destination_type=ospf_ct,
                destination_id=ospf.pk,
                source_protocol='connected',
                metric_type='2',
                route_map=cls.route_map,
            ),
            Redistribution(
                destination_type=ospf_ct,
                destination_id=ospf.pk,
                source_protocol='static',
                source_ref='mgmt',
            ),
            Redistribution(
                destination_type=isis_ct,
                destination_id=isis.pk,
                source_protocol='connected',
                metric_type='internal',
            ),
        )
        Redistribution.objects.bulk_create(redistributions)

    def test_q(self):
        params = {'q': 'mgmt'}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_source_protocol(self):
        params = {'source_protocol': ['connected']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 2)

    def test_metric_type(self):
        params = {'metric_type': ['internal']}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)

    def test_route_map(self):
        params = {'route_map_id': [self.route_map.pk]}
        self.assertEqual(self.filterset(params, self.queryset).qs.count(), 1)
