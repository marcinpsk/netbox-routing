from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from dcim.models import Interface
from utilities.testing import create_test_device

from netbox_routing.models.bgp import *
from netbox_routing.tests.base import *
from netbox_routing.tests.bgp.base import *

__all__ = ('BGPRouterTestCase',)


class BGPRouterTestCase(ASNMixin, TestCase):
    model = BGPRouter

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_model(self):
        name = 'BGP Router 1'
        instance = self.model(
            name=name,
            asn=self.asn,
        )
        instance.full_clean()
        instance.save()
        self.assertIsInstance(instance, self.model)
        self.assertEqual(instance.__str__(), f'{name} ({self.asn})')
        self.assertEqual(instance.asn, self.asn)

    def test_unique_together(self):

        name = 'BGP Router 1'
        instance = self.model(
            name=name,
            asn=self.asn,
        )
        instance.full_clean()
        instance.save()


class BGPScopeTestCase(BGPRouterMixin, VRFMixin, TestCase):
    model = BGPScope

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_model(self):
        instance = self.model(
            router=self.router,
        )
        instance.full_clean()
        instance.save()
        self.assertIsInstance(instance, self.model)
        self.assertEqual(instance.__str__(), f'{self.router}: Global VRF')
        self.assertEqual(instance.router, self.router)

    def test_model_with_vrf(self):
        instance = self.model(
            router=self.router,
            vrf=self.vrf,
        )
        instance.full_clean()
        instance.save()
        self.assertIsInstance(instance, self.model)
        self.assertEqual(instance.__str__(), f'{self.router}: {self.vrf}')
        self.assertEqual(instance.router, self.router)
        self.assertEqual(instance.vrf, self.vrf)

    def test_unique_together(self):
        instance = self.model(
            router=self.router,
        )
        instance.full_clean()
        instance.save()

        instance = self.model(
            router=self.router,
            vrf=self.vrf,
        )
        instance.full_clean()
        instance.save()

        instance = self.model(
            router=self.router,
        )

        with self.assertRaises(ValidationError):
            instance.full_clean()
        with self.assertRaises(IntegrityError):
            instance.save()


class BGPAddressFamilyTestCase(BGPScopeMixin, TestCase):
    model = BGPAddressFamily

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_model(self):
        instance = self.model(scope=self.scope, address_family='ipv4-unicast')
        instance.full_clean()
        instance.save()
        self.assertIsInstance(instance, self.model)
        self.assertEqual(instance.scope, self.scope)
        self.assertEqual(instance.address_family, 'ipv4-unicast')

    def test_model_invalid_af(self):
        instance = self.model(
            scope=self.scope,
            address_family='invalid',
        )
        with self.assertRaises(ValidationError):
            instance.full_clean()

    def test_unique_together(self):
        instance = self.model(
            scope=self.scope,
            address_family='ipv4-unicast',
        )
        instance.full_clean()
        instance.save()

        instance = self.model(
            scope=self.scope,
            address_family='ipv6-unicast',
        )
        instance.full_clean()
        instance.save()

        instance = self.model(
            scope=self.scope,
            address_family='ipv4-unicast',
        )

        with self.assertRaises(ValidationError):
            instance.full_clean()
        with self.assertRaises(IntegrityError):
            instance.save()


class BGPPeerTestCase(
    BGPScopeMixin,
    AddressesMixin,
    TestCase,
):
    model = BGPPeer

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_model(self):
        instance = self.model(
            name='Test Peer', scope=self.scope, peer=self.peer_address
        )
        instance.full_clean()
        instance.save()
        self.assertIsInstance(instance, self.model)
        self.assertEqual(instance.scope, self.scope)
        self.assertEqual(instance.peer, self.peer_address)

    def test_update_source_interface(self):
        """update_source holds a dcim.Interface (IOS / IOS-XR update-source)
        independently of the IPAddress source (Junos / Nokia local-address)."""
        device = create_test_device(name='Test Update-Source Device')
        loopback = Interface.objects.create(
            device=device, name='Loopback0', type='virtual'
        )
        instance = self.model(
            name='Update-Source Peer',
            scope=self.scope,
            peer=self.peer_address,
            source=self.source_address,
            update_source=loopback,
        )
        instance.full_clean()
        instance.save()

        instance.refresh_from_db()
        self.assertEqual(instance.source, self.source_address)
        self.assertEqual(instance.update_source, loopback)
        self.assertEqual(instance.update_source.name, 'Loopback0')

    def test_unique_together(self):
        instance = self.model(
            name='Test Peer', scope=self.scope, peer=self.peer_address
        )
        instance.full_clean()
        instance.save()

        instance = self.model(
            name='Test Peer', scope=self.scope, peer=self.peer_address
        )

        with self.assertRaises(ValidationError):
            instance.full_clean()
        with self.assertRaises(IntegrityError):
            instance.save()


class BGPPeerAddressFamilyTestCase(
    BGPPeerMixin,
    BGPAddressFamilyMixin,
    TestCase,
):
    model = BGPPeerAddressFamily

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_model(self):
        instance = self.model(
            assigned_object=self.peer,
            address_family=self.af,
        )
        instance.full_clean()
        instance.save()
        self.assertIsInstance(instance, self.model)
        self.assertEqual(instance.assigned_object, self.peer)
        self.assertEqual(instance.address_family, self.af)

    def test_unique_together(self):
        instance = self.model(
            assigned_object=self.peer,
            address_family=self.af,
        )
        instance.full_clean()
        instance.save()

        instance = self.model(
            assigned_object=self.peer,
            address_family=self.af,
        )

        with self.assertRaises(ValidationError):
            instance.full_clean()
        with self.assertRaises(IntegrityError):
            instance.save()


class BGPPeerTemplateTestCase(
    BGPAddressFamilyMixin,
    TestCase,
):
    model = BGPPeerTemplate

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_model(self):
        instance = self.model(
            name='Peer Template',
        )
        instance.full_clean()
        instance.save()
        self.assertIsInstance(instance, self.model)
        self.assertEqual(instance.__str__(), instance.name)

    def test_unique_together(self):
        instance = self.model(
            name='Peer Template',
            remote_as=self.asn,
        )
        instance.full_clean()
        instance.save()

        instance = self.model(
            name='Peer Template',
            remote_as=self.asn,
        )

        with self.assertRaises(ValidationError):
            instance.full_clean()
        with self.assertRaises(IntegrityError):
            instance.save()


class BGPPolicyTemplateTestCase(
    BGPAddressFamilyMixin,
    TestCase,
):
    model = BGPPolicyTemplate

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_model(self):
        instance = self.model(
            name='Policy Template',
        )
        instance.full_clean()
        instance.save()
        self.assertIsInstance(instance, self.model)
        self.assertEqual(instance.__str__(), instance.name)

    def test_unique_together(self):
        instance = self.model(
            name='Policy Template',
        )
        instance.full_clean()
        instance.save()

        instance = self.model(
            name='Policy Template',
        )

        with self.assertRaises(ValidationError):
            instance.full_clean()
        with self.assertRaises(IntegrityError):
            instance.save()


class BGPSessionTemplateTestCase(
    BGPAddressFamilyMixin,
    TestCase,
):
    model = BGPSessionTemplate

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_model(self):
        instance = self.model(
            name='Session Template',
        )
        instance.full_clean()
        instance.save()
        self.assertIsInstance(instance, self.model)
        self.assertEqual(instance.__str__(), instance.name)

    def test_unique_together(self):
        instance = self.model(
            name='Session Template',
        )
        instance.full_clean()
        instance.save()

        instance = self.model(
            name='Session Template',
        )

        with self.assertRaises(ValidationError):
            instance.full_clean()
        with self.assertRaises(IntegrityError):
            instance.save()


class BFDProfileTestCase(
    TestCase,
):
    model = BFDProfile

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_model(self):
        instance = self.model(
            name='Test BFD Profile X',
            min_rx_int=60,
            min_tx_int=60,
            multiplier=3,
        )
        instance.full_clean()
        instance.save()
        self.assertIsInstance(instance, self.model)
        self.assertEqual(instance.__str__(), instance.name)

    def test_unique_together(self):
        instance = self.model(
            name='Test BFD Profile X',
            min_rx_int=60,
            min_tx_int=60,
            multiplier=3,
        )
        instance.full_clean()
        instance.save()

        instance = self.model(
            name='Test BFD Profile X',
            min_rx_int=60,
            min_tx_int=60,
            multiplier=3,
        )

        with self.assertRaises(ValidationError):
            instance.full_clean()
        with self.assertRaises(IntegrityError):
            instance.save()


class BGPAddressFamilyChoicesTestCase(TestCase):
    """Guard the AFI choice vocabulary the NSO pipeline round-trips through this model."""

    def test_labeled_unicast_are_distinct_choices(self):
        # BGP-LU is a different family than plain unicast (IOS-XR/Junos/Nokia all model it
        # separately); the sync pipeline must be able to store it without folding.
        from netbox_routing.choices.bgp import BGPAddressFamilyChoices

        values = dict(BGPAddressFamilyChoices.CHOICES)
        self.assertIn('ipv4-labeled-unicast', values)
        self.assertIn('ipv6-labeled-unicast', values)

    def test_every_declared_constant_is_a_choice(self):
        # Regression guard: the VPNv4-Multicast row accidentally reused the VPNV4_UNICAST
        # constant, so 'vpnv4-multicast' was declared but never selectable.
        from netbox_routing.choices.bgp import BGPAddressFamilyChoices as C

        values = {v for v, _label in C.CHOICES}
        declared = {
            getattr(C, name)
            for name in dir(C)
            if name.isupper()
            and name != 'CHOICES'
            and isinstance(getattr(C, name), str)
        }
        self.assertLessEqual(declared, values)
