from django.urls import reverse
from netaddr.ip import IPAddress
from rest_framework import status

from ipam.models import VRF
from utilities.testing import APITestCase, APIViewTestCases, create_test_device

from netbox_routing.models import StaticRoute
from netbox_routing.tests.base import IPAddressFieldMixin

__all__ = (
    'StaticRouteTestCase',
    'StaticRouteRefusalAPITestCase',
)


class StaticRouteTestCase(IPAddressFieldMixin, APIViewTestCases.APIViewTestCase):
    model = StaticRoute
    view_namespace = "plugins-api:netbox_routing"
    brief_fields = [
        'description',
        'display',
        'id',
        'name',
        'next_hop',
        'prefix',
        'url',
    ]

    bulk_update_data = {'metric': 5}

    @classmethod
    def setUpTestData(cls):

        device = create_test_device(name='Test Device')
        vrf = VRF.objects.create(name='Test VRF')

        nh = IPAddress('10.10.10.1')

        routes = (
            StaticRoute(name='Test Route 1', vrf=vrf, prefix='0.0.0.0/0', next_hop=nh),
            StaticRoute(
                name='Test Route 2', vrf=None, prefix='1.1.1.1/32', next_hop=nh
            ),
            StaticRoute(name='Test Route 3', vrf=vrf, prefix='2.2.2.2/32', next_hop=nh),
        )
        StaticRoute.objects.bulk_create(routes)

        routes[0].devices.set([device])
        routes[1].devices.set([device])
        routes[2].devices.set([device])

        cls.create_data = [
            {
                'name': 'Default Route',
                'devices': [device.pk],
                'vrf': vrf.pk,
                'prefix': '0.0.0.0/0',
                'next_hop': '10.10.10.2',
                'metric': 1,
                'permanent': True,
            },
            {
                'name': 'Google DNS',
                'devices': [device.pk],
                'vrf': None,
                'prefix': '4.4.4.4/32',
                'next_hop': '10.10.10.1',
                'metric': 1,
                'permanent': True,
            },
            {
                'name': 'One dot one dot one dot one',
                'devices': [device.pk],
                'vrf': None,
                'prefix': '1.1.1.0/24',
                'next_hop': '10.10.10.1',
                'metric': 1,
                'permanent': True,
            },
        ]


class StaticRouteRefusalAPITestCase(APITestCase):
    """The REST path refuses the same shared-device triple the form does.

    Without this the API returns 200 over an intent the rest of the stack rejects — DRF
    never calls ``full_clean()``, so a model-level check would not run here at all.
    """

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='API Refusal Device 1')
        cls.other_device = create_test_device(name='API Refusal Device 2')

    def _route(self, devices=None, **kwargs):
        fields = {'prefix': '10.0.0.0/24', 'next_hop': IPAddress('10.10.10.1')}
        fields.update(kwargs)
        route = StaticRoute.objects.create(**fields)
        route.devices.set(devices if devices is not None else [self.device])
        return route

    def _payload(self, **overrides):
        payload = {
            'name': 'API Route',
            'devices': [self.device.pk],
            'vrf': None,
            'prefix': '10.0.0.0/24',
            'next_hop': '10.10.10.1',
            'metric': 1,
        }
        payload.update(overrides)
        return payload

    def test_create_with_a_duplicate_triple_on_a_shared_device_is_refused(self):
        self.add_permissions('netbox_routing.add_staticroute')
        self._route()

        url = reverse('plugins-api:netbox_routing-api:staticroute-list')
        response = self.client.post(url, self._payload(), format='json', **self.header)

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('prefix', response.data)

    def test_create_on_a_disjoint_device_is_allowed(self):
        self.add_permissions('netbox_routing.add_staticroute')
        self._route(devices=[self.other_device])

        url = reverse('plugins-api:netbox_routing-api:staticroute-list')
        response = self.client.post(url, self._payload(), format='json', **self.header)

        self.assertHttpStatus(response, status.HTTP_201_CREATED)

    def test_patch_landing_on_another_routes_triple_is_refused(self):
        self.add_permissions('netbox_routing.change_staticroute')
        self._route()
        edited = self._route(next_hop=IPAddress('10.10.10.2'))

        url = reverse(
            'plugins-api:netbox_routing-api:staticroute-detail', args=[edited.pk]
        )
        response = self.client.patch(
            url, {'next_hop': '10.10.10.1'}, format='json', **self.header
        )

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertIn('prefix', response.data)

    def test_patch_keeping_its_own_triple_is_allowed(self):
        self.add_permissions('netbox_routing.change_staticroute')
        edited = self._route()

        url = reverse(
            'plugins-api:netbox_routing-api:staticroute-detail', args=[edited.pk]
        )
        response = self.client.patch(url, {'metric': 7}, format='json', **self.header)

        self.assertHttpStatus(response, status.HTTP_200_OK)

    def test_bulk_create_with_two_identical_triples_on_one_device_is_refused(self):
        """One list POST validates every child before any is saved, so a child's own
        clash query cannot see its siblings."""
        self.add_permissions('netbox_routing.add_staticroute')

        url = reverse('plugins-api:netbox_routing-api:staticroute-list')
        response = self.client.post(
            url,
            [self._payload(name='First'), self._payload(name='Second')],
            format='json',
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(StaticRoute.objects.count(), 0)
        # DRF's list error contract: one entry per submitted item, in order, with the
        # field's messages as a list. A sparse dict keyed by index would not parse.
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0], {})
        self.assertIsInstance(response.data[1]['prefix'], list)

    def test_bulk_create_of_distinct_triples_is_allowed(self):
        self.add_permissions('netbox_routing.add_staticroute')

        url = reverse('plugins-api:netbox_routing-api:staticroute-list')
        response = self.client.post(
            url,
            [
                self._payload(name='First'),
                self._payload(name='Second', next_hop='10.10.10.2'),
            ],
            format='json',
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(StaticRoute.objects.count(), 2)

    def test_bulk_create_of_one_triple_on_disjoint_devices_is_allowed(self):
        self.add_permissions('netbox_routing.add_staticroute')

        url = reverse('plugins-api:netbox_routing-api:staticroute-list')
        response = self.client.post(
            url,
            [
                self._payload(name='First'),
                self._payload(name='Second', devices=[self.other_device.pk]),
            ],
            format='json',
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_201_CREATED)
        self.assertEqual(StaticRoute.objects.count(), 2)

    def test_bulk_patch_does_not_run_the_cross_item_check(self):
        """NetBox validates a bulk PATCH object by object with single-object serializers.

        The list serializer never sees it, so its cross-item check — which reads a
        partial payload's absent triple as blank — cannot fire false duplicates here.
        """
        self.add_permissions('netbox_routing.change_staticroute')
        first = self._route()
        second = self._route(next_hop=IPAddress('10.10.10.2'))

        url = reverse('plugins-api:netbox_routing-api:staticroute-list')
        response = self.client.patch(
            url,
            [
                {'id': first.pk, 'devices': [self.device.pk]},
                {'id': second.pk, 'devices': [self.device.pk]},
            ],
            format='json',
            **self.header,
        )

        self.assertHttpStatus(response, status.HTTP_200_OK)
