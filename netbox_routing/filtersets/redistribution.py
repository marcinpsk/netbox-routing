# SPDX-License-Identifier: Apache-2.0

import django_filters
from django.db.models import Q
from django.utils.translation import gettext as _

from netbox.filtersets import NetBoxModelFilterSet
from utilities.filtersets import register_filterset

from netbox_routing.models.objects import RouteMap
from netbox_routing.models.redistribution import (
    MetricTypeChoices,
    Redistribution,
    SourceProtocolChoices,
)

__all__ = ('RedistributionFilterSet',)


@register_filterset
class RedistributionFilterSet(NetBoxModelFilterSet):
    source_protocol = django_filters.MultipleChoiceFilter(
        choices=SourceProtocolChoices,
        label=_('Source Protocol'),
    )
    metric_type = django_filters.MultipleChoiceFilter(
        choices=MetricTypeChoices,
        label=_('Metric Type'),
    )
    route_map_id = django_filters.ModelMultipleChoiceFilter(
        field_name='route_map',
        queryset=RouteMap.objects.all(),
        label=_('Route Map (ID)'),
    )

    class Meta:
        model = Redistribution
        fields = (
            'id',
            'destination_type',
            'destination_id',
            'source_protocol',
            'source_ref',
            'metric',
            'metric_type',
            'route_map_id',
        )

    def search(self, queryset, name, value):
        if not value.strip():
            return queryset
        qs_filter = Q(source_protocol__icontains=value) | Q(source_ref__icontains=value)
        return queryset.filter(qs_filter).distinct()
