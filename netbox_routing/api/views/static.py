from django.db import transaction
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty

from dcim.models import Device
from netbox.api.viewsets import NetBoxModelViewSet
from netbox_routing import filtersets
from netbox_routing.api.serializers import StaticRouteSerializer
from netbox_routing.helpers.static import lock_static_route_devices
from netbox_routing.models import StaticRoute


class StaticRouteViewSet(NetBoxModelViewSet):
    queryset = StaticRoute.objects.all()
    serializer_class = StaticRouteSerializer
    filterset_class = filtersets.StaticRouteFilterSet

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
        with transaction.atomic():
            lock_static_route_devices(self._validated_bulk_devices(data))
            return super().perform_bulk_create(data)

    def perform_bulk_update(self, objects, update_data, partial):
        with transaction.atomic():
            stored_routes = list(objects.select_for_update(of=('self',)).order_by('pk'))
            devices = list(
                Device.objects.filter(static_routes__in=stored_routes).distinct()
            )
            devices.extend(self._validated_bulk_devices(update_data.values()))
            lock_static_route_devices(devices)
            return super().perform_bulk_update(objects, update_data, partial)
