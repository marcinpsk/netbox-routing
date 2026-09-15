from django.db import OperationalError, connections, router, transaction
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from core.signals import clear_events
from dcim.models import Device
from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing import filtersets
from netbox_routing.api.serializers import StaticRouteSerializer
from netbox_routing.helpers.static import lock_static_route_devices
from netbox_routing.models import StaticRoute

_DEADLOCK_SQLSTATE = '40P01'
_WRITE_ATTEMPTS = 3


def _retry_deadlocked_write(operation, using, sender):
    if connections[using].in_atomic_block:
        return operation()

    for attempt in range(_WRITE_ATTEMPTS):
        try:
            return operation()
        except OperationalError as error:
            cause = error.__cause__
            sqlstate = getattr(cause, 'sqlstate', None) or getattr(
                cause, 'pgcode', None
            )
            if sqlstate != _DEADLOCK_SQLSTATE:
                raise
            clear_events.send(sender=sender)
            if attempt == _WRITE_ATTEMPTS - 1:
                raise


class StaticRouteViewSet(NetBoxModelViewSet):
    queryset = StaticRoute.objects.all()
    serializer_class = StaticRouteSerializer
    filterset_class = filtersets.StaticRouteFilterSet

    def _retry_write(self, operation, using):
        return _retry_deadlocked_write(operation, using, self)

    def perform_create(self, serializer):
        using = router.db_for_write(self.queryset.model)
        if connections[using].in_atomic_block:
            return super().perform_create(serializer)

        def write():
            attempt_serializer = self.get_serializer(
                data=serializer.initial_data,
            )
            attempt_serializer.is_valid(raise_exception=True)
            super(StaticRouteViewSet, self).perform_create(attempt_serializer)
            serializer.instance = attempt_serializer.instance

        return self._retry_write(write, using)

    def perform_update(self, serializer):
        using = router.db_for_write(self.queryset.model)
        if connections[using].in_atomic_block:
            return super().perform_update(serializer)

        def write():
            instance = self.get_queryset().get(pk=serializer.instance.pk)
            if hasattr(instance, 'snapshot'):
                instance.snapshot()
            attempt_serializer = self.get_serializer(
                instance,
                data=serializer.initial_data,
                partial=serializer.partial,
            )
            attempt_serializer.is_valid(raise_exception=True)
            super(StaticRouteViewSet, self).perform_update(attempt_serializer)
            serializer.instance = attempt_serializer.instance

        return self._retry_write(write, using)

    def _validated_bulk_devices(self, data):
        devices = []
        field = self.get_serializer().fields['devices']
        for item in data:
            if not isinstance(item, dict):
                continue
            value = field.get_value(item)
            if value is empty:
                continue
            try:
                item_devices = field.run_validation(value)
            except ValidationError:
                continue
            devices.extend(item_devices or ())
        return devices

    def perform_bulk_create(self, data):
        using = router.db_for_write(self.queryset.model)

        def write():
            with transaction.atomic(using=using):
                lock_static_route_devices(self._validated_bulk_devices(data))
                return super(StaticRouteViewSet, self).perform_bulk_create(data)

        return self._retry_write(write, using)

    def perform_bulk_update(self, objects, update_data, partial):
        using = router.db_for_write(self.queryset.model)

        def write():
            attempt_objects = objects.all()
            with transaction.atomic(using=using):
                stored_routes = list(
                    attempt_objects.select_for_update(of=('self',)).order_by('pk')
                )
                devices = list(
                    Device.objects.filter(static_routes__in=stored_routes).distinct()
                )
                devices.extend(self._validated_bulk_devices(update_data.values()))
                lock_static_route_devices(devices)
                return super(StaticRouteViewSet, self).perform_bulk_update(
                    attempt_objects,
                    update_data,
                    partial,
                )

        return self._retry_write(write, using)
