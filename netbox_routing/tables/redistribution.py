# SPDX-License-Identifier: Apache-2.0

import django_tables2 as tables
from django.utils.translation import gettext as _

from netbox.tables import NetBoxTable, columns

from netbox_routing.models.redistribution import Redistribution

__all__ = ('RedistributionTable',)


class RedistributionTable(NetBoxTable):
    destination_type = columns.ContentTypeColumn(verbose_name=_('Destination Type'))
    destination = tables.Column(
        linkify=True, orderable=False, verbose_name=_('Destination')
    )
    source_protocol = tables.Column(verbose_name=_('Source Protocol'))
    source_ref = tables.Column(verbose_name=_('Source Reference'))
    route_map = tables.Column(linkify=True, verbose_name=_('Route Map'))
    metric_type = tables.Column(verbose_name=_('Metric Type'))

    class Meta(NetBoxTable.Meta):
        model = Redistribution
        fields = (
            'pk',
            'id',
            'destination_type',
            'destination',
            'source_protocol',
            'source_ref',
            'route_map',
            'metric',
            'metric_type',
            'description',
        )
        default_columns = (
            'pk',
            'id',
            'destination',
            'source_protocol',
            'source_ref',
            'route_map',
            'metric',
        )
