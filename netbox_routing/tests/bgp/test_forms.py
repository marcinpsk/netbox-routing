import json

from django.test import TestCase
from netaddr import IPNetwork

from dcim.models import Interface, Site
from ipam.models import IPAddress
from utilities.testing import create_test_device

from netbox_routing.forms.model_objects.bgp import BGPPeerForm, BGPRouterForm
from netbox_routing.models import BGPPeer, BGPRouter, BGPScope
from netbox_routing.tests.base import ASNMixin

__all__ = ('BGPFormTestCase',)


class BGPFormTestCase(ASNMixin, TestCase):

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.device = create_test_device(name='BGP Form Device 1')
        cls.other_device = create_test_device(name='BGP Form Device 2')
        cls.interface = Interface.objects.create(
            device=cls.device, name='Loopback0', type='virtual'
        )
        cls.other_interface = Interface.objects.create(
            device=cls.other_device, name='Loopback0', type='virtual'
        )
        router = BGPRouter.objects.create(
            name='BGP Form Router', asn=cls.asn, assigned_object=cls.device
        )
        cls.scope = BGPScope.objects.create(router=router)
        cls.peer = IPAddress.objects.create(address=IPNetwork('192.0.2.2/32'))

    def test_router_form_saves_router_id_on_router(self):
        form = BGPRouterForm(
            data={
                'name': 'Router With ID',
                'asn': self.asn.pk,
                'router_id': '192.0.2.1',
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        router = form.save()
        router.refresh_from_db()
        self.assertEqual(str(router.router_id), '192.0.2.1')
        self.assertFalse(router.settings.filter(key='router_id').exists())
