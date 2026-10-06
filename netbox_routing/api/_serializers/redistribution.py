# SPDX-License-Identifier: Apache-2.0

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from netbox.api.fields import ContentTypeField
from netbox.api.gfk_fields import GFKSerializerField
from netbox.api.serializers import NetBoxModelSerializer

from netbox_routing.api._serializers.objects import RouteMapSerializer
from netbox_routing.constants.redistribution import REDISTRIBUTION_DESTINATION_MODELS
from netbox_routing.models.redistribution import Redistribution

__all__ = ('RedistributionSerializer',)


class RedistributionSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing-api:redistribution-detail'
    )
    destination_type = ContentTypeField(
        queryset=ContentType.objects.filter(REDISTRIBUTION_DESTINATION_MODELS),
    )
    destination = GFKSerializerField(read_only=True)
    route_map = RouteMapSerializer(nested=True, required=False, allow_null=True)

    class Meta:
        model = Redistribution
        fields = (
            'url',
            'id',
            'display',
            'destination_type',
            'destination_id',
            'destination',
            'source_protocol',
            'source_ref',
            'route_map',
            'metric',
            'metric_type',
            'description',
            'comments',
            'tags',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'destination',
            'source_protocol',
            'source_ref',
        )
