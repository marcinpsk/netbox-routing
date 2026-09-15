from django.utils.translation import gettext as _
from rest_framework import serializers

from dcim.api.serializers_.devices import DeviceSerializer
from ipam.api.serializers_.vrfs import VRFSerializer
from netbox.api.serializers import NetBoxModelSerializer

from netbox_routing.api.field_serializers import IPAddressField
from netbox_routing.helpers.static import (
    interface_only_conversion_errors,
    shared_device_triple_errors,
    stored_route,
    triple_key,
)
from netbox_routing.models import StaticRoute

__all__ = (
    'StaticRouteListSerializer',
    'StaticRouteSerializer',
)


class StaticRouteListSerializer(serializers.ListSerializer):
    """Cross-item half of the shared-device triple refusal.

    A list POST validates every child before saving any, so a child's clash query sees
    the database without its siblings and two identical entries would both be created.
    """

    def to_internal_value(self, data):
        # Not validate(): ListSerializer.run_validation funnels anything validate() raises
        # through as_serializer_error, which buries a list under non_field_errors. Raising
        # from here keeps DRF's list contract — one entry per item, in order.
        attrs = super().to_internal_value(data)

        errors = [{} for _ in attrs]
        seen = {}
        for index, item in enumerate(attrs):
            key = triple_key(item.get('vrf'), item.get('prefix'), item.get('next_hop'))
            devices = {
                getattr(device, 'pk', device) for device in item.get('devices') or ()
            }
            for prior_index, prior_devices in seen.setdefault(key, []):
                if devices & prior_devices:
                    errors[index] = {
                        'prefix': [
                            _(
                                'Entry %(prior)s of this request already assigns this '
                                'route to one of the same devices. A device cannot hold '
                                'the same route twice.'
                            )
                            % {'prior': prior_index}
                        ]
                    }
                    break
            seen[key].append((index, devices))

        if any(errors):
            raise serializers.ValidationError(errors)

        return attrs


class StaticRouteSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing-api:staticroute-detail'
    )
    devices = DeviceSerializer(many=True, nested=True, required=False, allow_null=True)
    vrf = VRFSerializer(nested=True, required=False, allow_null=True)
    next_hop = IPAddressField()

    class Meta:
        model = StaticRoute
        list_serializer_class = StaticRouteListSerializer
        fields = (
            'url',
            'id',
            'display',
            'devices',
            'vrf',
            'prefix',
            'next_hop',
            'name',
            'metric',
            'tag',
            'permanent',
            'description',
            'comments',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'name',
            'prefix',
            'next_hop',
            'description',
        )

    def validate(self, attrs):
        attrs = super().validate(attrs)

        stored = stored_route(self.instance)
        devices = attrs.get('devices')
        if devices is None:
            devices = list(stored.devices.all()) if stored is not None else []

        errors = {}
        errors.update(
            shared_device_triple_errors(
                stored,
                self._pending(attrs, 'vrf'),
                self._pending(attrs, 'prefix'),
                self._pending(attrs, 'next_hop'),
                devices,
            )
        )
        # interface_next_hop is not a serializer field (and next_hop is required), so this
        # cannot fire over the wire today; it stays here so the two write paths share one
        # rule rather than diverging the day the field is exposed.
        errors.update(
            interface_only_conversion_errors(
                stored,
                self._pending(attrs, 'next_hop'),
                self._pending(attrs, 'interface_next_hop'),
            )
        )
        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    def _pending(self, attrs, field):
        """The value this write will leave on the row — a PATCH may not carry it at all."""
        if field in attrs:
            return attrs[field]
        return (
            getattr(self.instance, field, None) if self.instance is not None else None
        )

    def create(self, validated_data):
        devices = validated_data.pop('devices', None)
        instance = super().create(validated_data)

        return self._update_devices(instance, devices)

    def update(self, instance, validated_data):
        devices = validated_data.pop('devices', None)
        instance = super().update(instance, validated_data)

        return self._update_devices(instance, devices)

    def _update_devices(self, instance: StaticRoute, devices: object) -> StaticRoute:
        if devices:
            instance.devices.set(devices)
        elif devices is not None:
            instance.devices.clear()

        return instance
