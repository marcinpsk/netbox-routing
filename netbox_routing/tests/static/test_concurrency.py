import threading
from concurrent.futures import ThreadPoolExecutor

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import connection
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError as DRFValidationError

from utilities.testing import create_test_device

from netbox_routing.api._serializers.static import StaticRouteSerializer
from netbox_routing.forms import StaticRouteForm
from netbox_routing.models import StaticRoute

__all__ = ('StaticRouteConcurrencyTestCase',)


class StaticRouteConcurrencyTestCase(TransactionTestCase):

    def setUp(self):
        self.device = create_test_device(name='Concurrent Route Device')
        self.other_device = create_test_device(name='Other Concurrent Route Device')

    def _payload(self):
        return {
            'name': 'Concurrent Route',
            'devices': [self.device.pk],
            'vrf': None,
            'prefix': '198.18.0.0/24',
            'next_hop': '192.0.2.1',
            'metric': 1,
        }

    def _run_concurrent_writes(self, build_writer, validation_errors):
        barrier = threading.Barrier(2)

        def write_route(index):
            try:
                writer = build_writer(index)
                if not writer.is_valid():
                    raise AssertionError(writer.errors)

                barrier.wait(timeout=10)
                try:
                    writer.save()
                except validation_errors as error:
                    return 'refused', error
                return 'created', None
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(write_route, index) for index in range(2)]
            results = [future.result(timeout=15) for future in futures]
        self.assertCountEqual(
            [outcome for outcome, _ in results], ['created', 'refused']
        )
        refusal = next(error for outcome, error in results if outcome == 'refused')
        errors = (
            refusal.message_dict
            if isinstance(refusal, DjangoValidationError)
            else refusal.detail
        )
        self.assertIn('prefix', errors)

    def test_concurrent_form_creates_refuse_one_route(self):
        self._run_concurrent_writes(
            lambda _: StaticRouteForm(data=self._payload()),
            (DjangoValidationError,),
        )
        self.assertEqual(StaticRoute.objects.count(), 1)

    def test_concurrent_serializer_creates_refuse_one_route(self):
        self._run_concurrent_writes(
            lambda _: StaticRouteSerializer(data=self._payload()),
            (DRFValidationError,),
        )
        self.assertEqual(StaticRoute.objects.count(), 1)

    def test_concurrent_updates_use_one_locked_route_state(self):
        edited = StaticRoute.objects.create(
            prefix='198.18.1.0/24',
            next_hop='192.0.2.1',
        )
        edited.devices.add(self.device)
        clash = StaticRoute.objects.create(
            prefix='198.18.1.0/24',
            next_hop='192.0.2.2',
        )
        clash.devices.add(self.other_device)
        payloads = (
            {'next_hop': '192.0.2.2'},
            {'devices': [self.other_device.pk]},
        )

        def serializer(index):
            instance = StaticRoute.objects.get(pk=edited.pk)
            return StaticRouteSerializer(
                instance,
                data=payloads[index],
                partial=True,
            )

        self._run_concurrent_writes(serializer, (DRFValidationError,))
