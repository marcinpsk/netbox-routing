# SPDX-License-Identifier: Apache-2.0

from django import forms
from django.utils.translation import gettext as _

from netbox.forms import NetBoxModelFilterSetForm
from utilities.forms.fields import DynamicModelMultipleChoiceField, TagFilterField
from utilities.forms.rendering import FieldSet

from netbox_routing.models.objects import RouteMap
from netbox_routing.models.redistribution import (
    MetricTypeChoices,
    Redistribution,
    SourceProtocolChoices,
)

__all__ = ('RedistributionFilterForm',)


class RedistributionFilterForm(NetBoxModelFilterSetForm):
    model = Redistribution
    fieldsets = (
        FieldSet('q', 'filter_id', 'tag'),
        FieldSet(
            'source_protocol',
            'source_ref',
            'metric_type',
            'route_map_id',
            name=_('Attributes'),
        ),
    )
    source_protocol = forms.MultipleChoiceField(
        choices=SourceProtocolChoices,
        required=False,
        label=_('Source Protocol'),
    )
    source_ref = forms.CharField(
        required=False,
        label=_('Source Reference'),
    )
    metric_type = forms.MultipleChoiceField(
        choices=MetricTypeChoices,
        required=False,
        label=_('Metric Type'),
    )
    route_map_id = DynamicModelMultipleChoiceField(
        queryset=RouteMap.objects.all(),
        required=False,
        selector=True,
        label=_('Route Map'),
    )
    tag = TagFilterField(model)
