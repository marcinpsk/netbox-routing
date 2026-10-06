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

    def test_peer_update_source_must_belong_to_selected_device(self):
        form = BGPPeerForm(
            data={
                'name': 'BGP Form Peer',
                'scope': self.scope.pk,
                'peer': self.peer.pk,
                'device': self.device.pk,
                'update_source': self.other_interface.pk,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn('update_source', form.errors)

    def test_peer_update_source_accepts_selected_device_interface(self):
        form = BGPPeerForm(
            data={
                'name': 'BGP Form Peer',
                'scope': self.scope.pk,
                'peer': self.peer.pk,
                'device': self.device.pk,
                'update_source': self.interface.pk,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        peer = form.save()
        self.assertEqual(peer.update_source, self.interface)

    def test_peer_update_source_is_unconstrained_without_device(self):
        form = BGPPeerForm(
            data={
                'name': 'BGP Form Peer',
                'scope': self.scope.pk,
                'peer': self.peer.pk,
                'update_source': self.other_interface.pk,
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        peer = form.save()
        self.assertEqual(peer.update_source, self.other_interface)

    def test_peer_update_source_selector_depends_on_device(self):
        form = BGPPeerForm()

        str(form['update_source'])

        self.assertEqual(
            json.loads(
                form.fields['update_source'].widget.attrs['data-dynamic-params']
            ),
            [{'fieldName': 'device', 'queryParam': 'device_id'}],
        )
        self.assertEqual(
            form.fields['update_source'].widget.attrs['data-url'],
            '/api/dcim/interfaces/',
        )

    def test_existing_site_scoped_peer_keeps_update_source_on_edit(self):
        site = Site.objects.create(name='BGP Form Site', slug='bgp-form-site')
        router = BGPRouter.objects.create(
            name='BGP Site Router', asn=self.asn, assigned_object=site
        )
        scope = BGPScope.objects.create(router=router)
        peer = BGPPeer.objects.create(
            name='BGP Site Peer',
            scope=scope,
            peer=self.peer,
            update_source=self.interface,
        )
        unbound_form = BGPPeerForm(instance=peer)
        self.assertEqual(unbound_form.initial['device'], self.device.pk)
        form = BGPPeerForm(
            instance=peer,
            data={
                'name': peer.name,
                'scope': scope.pk,
                'peer': self.peer.pk,
                'update_source': self.interface.pk,
                'description': 'Updated description',
            },
        )

        self.assertTrue(form.is_valid(), form.errors)
        saved_peer = form.save()
        self.assertEqual(saved_peer.description, 'Updated description')
        self.assertEqual(saved_peer.update_source, self.interface)

    def test_peer_form_rejects_malformed_scope_without_crashing(self):
        form = BGPPeerForm(data={'scope': 'invalid'})

        self.assertFalse(form.is_valid())
        self.assertIn('scope', form.errors)

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
