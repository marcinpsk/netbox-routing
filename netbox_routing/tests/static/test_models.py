from django.db import IntegrityError, transaction
from django.test import TestCase

from ipam.models import VRF
from utilities.testing import create_test_device

from netbox_routing.helpers.static import STATIC_ROUTE_DEVICE_TRIPLE_CONSTRAINT
from netbox_routing.models import StaticRoute

__all__ = ('StaticRouteTestCase',)


class StaticRouteTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Static Route Constraint Device')
        cls.other_device = create_test_device(
            name='Other Static Route Constraint Device'
        )
        cls.vrf = VRF.objects.create(name='Static Route Constraint VRF')

    def _route(self, devices=None, **overrides):
        fields = {
            'prefix': '198.18.0.0/24',
            'next_hop': '192.0.2.1',
        }
        fields.update(overrides)
        route = StaticRoute.objects.create(**fields)
        if devices:
            route.devices.add(*devices)
        return route

    def test_adding_a_duplicate_null_triple_to_a_device_is_refused(self):
        self._route(
            devices=[self.device],
            next_hop=None,
            interface_next_hop='Ethernet1/1',
        )
        duplicate = self._route(
            next_hop=None,
            interface_next_hop='Ethernet1/2',
        )

        with (
            self.assertRaises(IntegrityError) as raised,
            transaction.atomic(),
        ):
            duplicate.devices.add(self.device)

        self.assertEqual(
            raised.exception.__cause__.diag.constraint_name,
            STATIC_ROUTE_DEVICE_TRIPLE_CONSTRAINT,
        )
        self.assertEqual(StaticRoute.objects.filter(devices=self.device).count(), 1)

    def test_moving_a_duplicate_triple_to_a_device_is_refused(self):
        self._route(devices=[self.device])
        duplicate = self._route(devices=[self.other_device])

        through = StaticRoute.devices.through
        with self.assertRaises(IntegrityError), transaction.atomic():
            through.objects.filter(
                staticroute=duplicate,
                device=self.other_device,
            ).update(device=self.device)

        self.assertEqual(duplicate.devices.get(), self.other_device)

    def test_updating_prefix_into_a_device_triple_is_refused(self):
        self._route(devices=[self.device])
        edited = self._route(
            devices=[self.device],
            prefix='198.18.1.0/24',
        )
        edited.prefix = '198.18.0.0/24'

        with self.assertRaises(IntegrityError), transaction.atomic():
            edited.save(update_fields=['prefix'])

    def test_updating_next_hop_into_a_device_triple_is_refused(self):
        self._route(devices=[self.device])
        edited = self._route(
            devices=[self.device],
            next_hop='192.0.2.2',
        )
        edited.next_hop = '192.0.2.1'

        with self.assertRaises(IntegrityError), transaction.atomic():
            edited.save(update_fields=['next_hop'])

    def test_updating_vrf_into_a_device_triple_is_refused(self):
        self._route(devices=[self.device])
        edited = self._route(devices=[self.device], vrf=self.vrf)
        edited.vrf = None

        with self.assertRaises(IntegrityError), transaction.atomic():
            edited.save(update_fields=['vrf'])

    def test_resaving_the_same_route_succeeds(self):
        route = self._route(devices=[self.device])

        route.save()

        self.assertEqual(route.devices.get(), self.device)
