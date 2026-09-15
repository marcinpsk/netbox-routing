import threading
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from time import monotonic, sleep

from django.contrib.auth import get_user_model
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TransactionTestCase
from django.urls import reverse
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.test import APIClient

from utilities.testing import create_test_device

from netbox_routing.api._serializers.static import StaticRouteSerializer
from netbox_routing.models import StaticRoute

__all__ = ('StaticRouteConcurrencyTestCase',)


class StaticRouteConcurrencyTestCase(TransactionTestCase):

    wait_timeout = 120

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

    def _migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(targets)

    def _remove_database_triggers(self):
        executor = MigrationExecutor(connection)
        current = executor.loader.graph.leaf_nodes('netbox_routing')
        self.addCleanup(self._migrate, current)
        executor.migrate([('netbox_routing', '0038_alter_community_community')])
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT tgname FROM pg_trigger WHERE tgname IN (%s, %s)",
                [
                    'netbox_routing_staticroute_devices_unique_triple',
                    'netbox_routing_staticroute_unique_triple_update',
                ],
            )
            self.assertEqual(cursor.fetchall(), [])

    def _backend_pid(self):
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_backend_pid()')
            return cursor.fetchone()[0]

    def _wait_until_blocked_by(self, contender_pid, blocker_pid, future):
        deadline = monotonic() + self.wait_timeout
        while monotonic() < deadline:
            if future.done():
                if error := future.exception():
                    details = f'{type(error).__name__}: {error}'
                else:
                    details = repr(future.result())
                self.fail(
                    'The contender completed before it waited for the row lock: '
                    f'{details}'
                )
            with connection.cursor() as cursor:
                cursor.execute(
                    'WITH RECURSIVE blockers(pid) AS ('
                    ' SELECT unnest(pg_blocking_pids(%s))'
                    ' UNION'
                    ' SELECT unnest(pg_blocking_pids(blockers.pid)) FROM blockers'
                    ') SELECT EXISTS(SELECT 1 FROM blockers WHERE pid = %s)',
                    [contender_pid, blocker_pid],
                )
                if cursor.fetchone()[0]:
                    return
            sleep(0.02)
        with connection.cursor() as cursor:
            cursor.execute(
                'SELECT state, wait_event_type, wait_event, query, pg_blocking_pids(pid) '
                'FROM pg_stat_activity WHERE pid = %s',
                [contender_pid],
            )
            activity = cursor.fetchone()
        self.fail(
            'The contender did not wait for the controlled row lock: '
            f'contender={contender_pid} blocker={blocker_pid} activity={activity}'
        )

    def _web_client(self, user):
        client = Client()
        client.force_login(user)
        return client

    def _api_client(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    def _run_while_locked(self, lock, operations, while_blocked=None):
        backend_pids = Queue()

        def run(operation):
            reported = False

            def report_ready():
                nonlocal reported
                reported = True
                backend_pids.put((self._backend_pid(), None))

            close_old_connections()
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT set_config('statement_timeout', %s, false)",
                        [f'{self.wait_timeout}s'],
                    )
                return operation(report_ready)
            except Exception as error:
                if not reported:
                    backend_pids.put((None, error))
                raise
            finally:
                connection.close()

        executor = ThreadPoolExecutor(max_workers=len(operations))
        futures = []
        try:
            with transaction.atomic():
                lock()
                blocker_pid = self._backend_pid()
                for operation in operations:
                    future = executor.submit(run, operation)
                    futures.append(future)
                    contender_pid, error = backend_pids.get(timeout=self.wait_timeout)
                    if error is not None:
                        raise error
                    self._wait_until_blocked_by(
                        contender_pid,
                        blocker_pid,
                        future,
                    )
                if while_blocked is not None:
                    while_blocked()

            return [future.result(timeout=self.wait_timeout) for future in futures]
        finally:
            executor.shutdown(wait=True, cancel_futures=True)

    def _clash_error(self, prefix, next_hop, device, route):
        return (
            f'A static route for {prefix} in the global routing table via '
            f'{next_hop} already exists on {device} ({route}). '
            'A device cannot hold the same route twice.'
        )

    def test_concurrent_form_creates_refuse_one_route(self):
        self._remove_database_triggers()
        user = get_user_model().objects.create_superuser(
            username='static-route-browser-race'
        )
        clients = [self._web_client(user) for _ in range(2)]
        url = reverse('plugins:netbox_routing:staticroute_add')

        def post_route(client):
            def operation(ready):
                ready()
                return client.post(url, {**self._payload(), 'vrf': ''})

            return operation

        responses = self._run_while_locked(
            lambda: type(self.device)
            .objects.select_for_update(no_key=True)
            .get(pk=self.device.pk),
            [post_route(client) for client in clients],
        )

        self.assertCountEqual(
            [response.status_code for response in responses], [200, 302]
        )
        refusal = next(
            response for response in responses if response.status_code == 200
        )
        route = StaticRoute.objects.get()
        expected = self._clash_error(
            '198.18.0.0/24',
            '192.0.2.1',
            self.device,
            route,
        )
        self.assertEqual(list(refusal.context['form'].errors['prefix']), [expected])

    def test_concurrent_serializer_creates_refuse_one_route(self):
        self._remove_database_triggers()

        def create_route(ready):
            serializer = StaticRouteSerializer(data=self._payload())
            if not serializer.is_valid():
                raise AssertionError(serializer.errors)
            ready()
            try:
                return 'created', serializer.save()
            except DRFValidationError as error:
                return 'refused', error

        results = self._run_while_locked(
            lambda: type(self.device)
            .objects.select_for_update(no_key=True)
            .get(pk=self.device.pk),
            [create_route, create_route],
        )

        self.assertCountEqual(
            [outcome for outcome, _ in results], ['created', 'refused']
        )
        route = StaticRoute.objects.get()
        expected = self._clash_error(
            '198.18.0.0/24',
            '192.0.2.1',
            self.device,
            route,
        )
        refusal = next(result for outcome, result in results if outcome == 'refused')
        self.assertEqual(refusal.detail, {'prefix': [expected]})

    def test_database_clash_save_error_uses_the_normal_field_shape(self):
        clash = StaticRoute.objects.create(
            prefix='198.18.0.0/24',
            next_hop='192.0.2.1',
        )

        def create_route(ready):
            serializer = StaticRouteSerializer(data=self._payload())
            if not serializer.is_valid():
                raise AssertionError(serializer.errors)
            ready()
            try:
                serializer.save()
            except DRFValidationError as error:
                return error
            raise AssertionError('The database clash was not refused.')

        def lock_route_table():
            with connection.cursor() as cursor:
                cursor.execute(
                    'LOCK TABLE netbox_routing_staticroute '
                    'IN SHARE ROW EXCLUSIVE MODE'
                )

        def insert_clashing_link():
            with connection.cursor() as cursor:
                cursor.execute('SET LOCAL session_replication_role = replica')
            StaticRoute.devices.through.objects.create(
                staticroute=clash,
                device=self.device,
            )

        refusal = self._run_while_locked(
            lock_route_table,
            [create_route],
            insert_clashing_link,
        )[0]

        expected = self._clash_error(
            '198.18.0.0/24',
            '192.0.2.1',
            self.device,
            clash,
        )
        self.assertEqual(refusal.detail, {'prefix': [expected]})

    def test_concurrent_api_bulk_creates_wait_for_the_application_device_lock(self):
        self._remove_database_triggers()
        user = get_user_model().objects.create_superuser(
            username='static-route-bulk-race'
        )
        clients = [self._api_client(user) for _ in range(2)]
        url = reverse('plugins-api:netbox_routing-api:staticroute-list')

        def create_routes(client):
            def operation(ready):
                ready()
                return client.post(url, [self._payload()], format='json')

            return operation

        responses = self._run_while_locked(
            lambda: type(self.device)
            .objects.select_for_update(no_key=True)
            .get(pk=self.device.pk),
            [create_routes(client) for client in clients],
        )

        self.assertCountEqual(
            [response.status_code for response in responses],
            [201, 400],
        )
        refusal = next(
            response for response in responses if response.status_code == 400
        )
        route = StaticRoute.objects.get()
        expected = self._clash_error(
            '198.18.0.0/24',
            '192.0.2.1',
            self.device,
            route,
        )
        self.assertEqual(
            refusal.data,
            {
                'detail': '1 of 1 objects could not be created.',
                'errors': [{'index': 0, 'errors': {'prefix': [expected]}}],
            },
        )

    def test_concurrent_updates_use_one_locked_route_state(self):
        self._remove_database_triggers()
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

        def update_route(index):
            def operation(ready):
                instance = StaticRoute.objects.get(pk=edited.pk)
                serializer = StaticRouteSerializer(
                    instance,
                    data=payloads[index],
                    partial=True,
                )
                if not serializer.is_valid():
                    raise AssertionError(serializer.errors)
                ready()
                try:
                    return 'updated', serializer.save()
                except DRFValidationError as error:
                    return 'refused', error

            return operation

        def lock_edited_route():
            with connection.cursor() as cursor:
                cursor.execute(
                    'SELECT id FROM netbox_routing_staticroute '
                    'WHERE id = %s FOR KEY SHARE',
                    [edited.pk],
                )
                cursor.fetchone()

        results = self._run_while_locked(
            lock_edited_route,
            [update_route(index) for index in range(2)],
        )

        self.assertCountEqual(
            [outcome for outcome, _ in results], ['updated', 'refused']
        )
        refusal = next(result for outcome, result in results if outcome == 'refused')
        expected = self._clash_error(
            '198.18.1.0/24',
            '192.0.2.2',
            self.other_device,
            clash,
        )
        self.assertEqual(refusal.detail, {'prefix': [expected]})

    def test_database_serializes_concurrent_device_assignments(self):
        routes = [
            StaticRoute.objects.create(
                prefix='198.18.1.0/24',
                next_hop='192.0.2.2',
            )
            for _ in range(2)
        ]
        barrier = threading.Barrier(2)

        def assign_device(route_pk):
            try:
                route = StaticRoute.objects.get(pk=route_pk)
                barrier.wait(timeout=10)
                try:
                    route.devices.add(self.device)
                except IntegrityError as error:
                    return 'refused', error
                return 'created', None
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(assign_device, route.pk) for route in routes]
            results = [future.result(timeout=15) for future in futures]

        self.assertCountEqual(
            [outcome for outcome, _ in results], ['created', 'refused']
        )
        self.assertEqual(StaticRoute.objects.filter(devices=self.device).count(), 1)
