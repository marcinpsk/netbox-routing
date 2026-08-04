import contextlib

from django.test import TestCase

from dcim.models import Device
from utilities.testing import create_test_device

from netbox_routing.forms import *
from netbox_routing.models import StaticRoute

__all__ = (
    'StaticRouteTestCase',
    'StaticRouteRefusalTestCase',
)


@contextlib.contextmanager
def _without_nso_plugin():
    """Run the body in the fork's own topology: netbox_nso_plugin absent, so StaticRoute
    carries no ``nso_states`` reverse accessor at all."""
    accessor = StaticRoute.__dict__.get('nso_states')
    if accessor is not None:
        delattr(StaticRoute, 'nso_states')
    try:
        yield
    finally:
        if accessor is not None:
            StaticRoute.nso_states = accessor


class StaticRouteTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Device 1')

    def test_staticroute(self):
        form = StaticRouteForm(
            data={
                'name': 'Route 1',
                'devices': [Device.objects.first().pk],
                'vrf': None,
                'prefix': '0.0.0.0/0',
                'next_hop': '10.10.10.1',
                'metric': 1,
            }
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(form.save())


class StaticRouteRefusalTestCase(TestCase):
    """The three refusals of the static-route form.

    (1) a second route with an identical triple on a shared device and (2) an edit landing
    one route on another route's live triple are unconditional; (3) converting an
    NSO-managed route to an interface-only next hop is scoped to routes the NSO plugin
    manages, and is inert when that plugin is not installed.
    """

    @classmethod
    def setUpTestData(cls):
        cls.device = create_test_device(name='Refusal Device 1')
        cls.other_device = create_test_device(name='Refusal Device 2')

    def _data(self, **overrides):
        data = {
            'name': 'Route',
            'devices': [self.device.pk],
            'vrf': None,
            'prefix': '10.0.0.0/24',
            'next_hop': '10.10.10.1',
            'metric': 1,
        }
        data.update(overrides)
        return data

    def _route(self, devices=None, **kwargs):
        fields = {'prefix': '10.0.0.0/24', 'next_hop': '10.10.10.1'}
        fields.update(kwargs)
        route = StaticRoute.objects.create(**fields)
        route.devices.set(devices if devices is not None else [self.device])
        return route

    # ── (1) a second route with an identical triple on a shared device ──────────

    def test_duplicate_triple_on_shared_device_is_refused(self):
        clash = self._route()

        form = StaticRouteForm(data=self._data())

        self.assertFalse(form.is_valid())
        message = str(form.errors['prefix'])
        self.assertIn('10.0.0.0/24', message)
        self.assertIn('10.10.10.1', message)
        self.assertIn(str(self.device), message)
        self.assertIn(str(clash), message)

    def test_duplicate_triple_on_a_disjoint_device_is_allowed(self):
        self._route(devices=[self.other_device])

        form = StaticRouteForm(data=self._data())

        self.assertTrue(form.is_valid(), form.errors)

    def test_a_differing_triple_on_a_shared_device_is_allowed(self):
        self._route()

        form = StaticRouteForm(data=self._data(next_hop='10.10.10.2'))

        self.assertTrue(form.is_valid(), form.errors)

    def test_a_null_next_hop_triple_is_compared_on_the_null(self):
        self._route(next_hop=None, interface_next_hop='GigabitEthernet0/0')

        form = StaticRouteForm(
            data=self._data(next_hop='', interface_next_hop='GigabitEthernet0/1')
        )

        self.assertFalse(form.is_valid())
        self.assertIn('prefix', form.errors)

    # ── (2) an edit landing one route on another route's live triple ────────────

    def test_edit_onto_another_routes_triple_is_refused(self):
        self._route()
        edited = self._route(next_hop='10.10.10.2')

        form = StaticRouteForm(data=self._data(), instance=edited)

        self.assertFalse(form.is_valid())
        self.assertIn('prefix', form.errors)

    def test_edit_keeping_its_own_triple_is_allowed(self):
        edited = self._route()

        form = StaticRouteForm(data=self._data(name='Renamed'), instance=edited)

        self.assertTrue(form.is_valid(), form.errors)

    def test_an_unrelated_edit_of_a_preexisting_duplicate_is_allowed(self):
        """Upstream removed the uniqueness constraint, so duplicates already exist.

        Renaming or re-metricing one of them is neither a second route nor an edit
        landing on another object's triple, so refusing it would be a fourth refusal.
        """
        self._route()
        edited = self._route()

        form = StaticRouteForm(
            data=self._data(name='Renamed', metric=9), instance=edited
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_adding_a_clash_free_device_to_a_preexisting_duplicate_is_allowed(self):
        """Only the devices this write actually adds are checked.

        Two legacy duplicates already share a device; assigning one of them to a further,
        conflict-free device must not rediscover the old clash on the shared one.
        """
        self._route()
        edited = self._route()

        form = StaticRouteForm(
            data=self._data(devices=[self.device.pk, self.other_device.pk]),
            instance=edited,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_adding_a_device_that_already_holds_the_triple_is_refused(self):
        self._route()
        edited = self._route(devices=[self.other_device])

        form = StaticRouteForm(
            data=self._data(devices=[self.device.pk, self.other_device.pk]),
            instance=edited,
        )

        self.assertFalse(form.is_valid())
        self.assertIn('prefix', form.errors)

    def test_edit_dropping_the_shared_device_is_allowed(self):
        self._route()
        edited = self._route(devices=[self.other_device], next_hop='10.10.10.2')

        form = StaticRouteForm(
            data=self._data(devices=[self.other_device.pk]), instance=edited
        )

        self.assertTrue(form.is_valid(), form.errors)

    # ── (3) interface-only conversion, and the plugin-absent topology ───────────

    def test_interface_only_conversion_is_allowed_without_an_nso_overlay(self):
        edited = self._route()

        form = StaticRouteForm(
            data=self._data(next_hop='', interface_next_hop='GigabitEthernet0/0'),
            instance=edited,
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_refusals_hold_and_the_nso_probe_is_inert_without_the_plugin(self):
        clash = self._route()
        edited = self._route(next_hop='10.10.10.2')

        with _without_nso_plugin():
            # (3) reaches the probe — an interface-only conversion of a stored route —
            # and must not raise merely because the accessor is absent.
            conversion = StaticRouteForm(
                data=self._data(
                    devices=[self.other_device.pk],
                    next_hop='',
                    interface_next_hop='GigabitEthernet0/0',
                ),
                instance=edited,
            )
            self.assertTrue(conversion.is_valid(), conversion.errors)

            duplicate = StaticRouteForm(data=self._data())
            self.assertFalse(duplicate.is_valid())
            self.assertIn(str(clash), str(duplicate.errors['prefix']))

            landing = StaticRouteForm(data=self._data(), instance=edited)
            self.assertFalse(landing.is_valid())
            self.assertIn('prefix', landing.errors)
