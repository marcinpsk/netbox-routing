# SPDX-License-Identifier: Apache-2.0

from django import forms
from django.utils.translation import gettext as _

from netbox.forms import NetBoxModelBulkEditForm
from utilities.forms.fields import CommentField, DynamicModelChoiceField
from utilities.forms.rendering import FieldSet

from netbox_routing.models.objects import RouteMap
from netbox_routing.models.redistribution import MetricTypeChoices, Redistribution

__all__ = ('RedistributionBulkEditForm',)


class RedistributionBulkEditForm(NetBoxModelBulkEditForm):
    route_map = DynamicModelChoiceField(
        queryset=RouteMap.objects.all(),
        required=False,
        selector=True,
        label=_('Route Map'),
    )
    metric = forms.IntegerField(label=_('Metric'), required=False)
    metric_type = forms.ChoiceField(
        label=_('Metric Type'),
        choices=[('', '---------')] + list(MetricTypeChoices.choices),
        required=False,
    )
    description = forms.CharField(
        label=_('Description'), max_length=200, required=False
    )
    comments = CommentField()

    model = Redistribution
    fieldsets = (
        FieldSet('route_map', 'metric', 'metric_type', name=_('Attributes')),
        FieldSet('description'),
    )
    nullable_fields = (
        'route_map',
        'metric',
        'metric_type',
        'description',
        'comments',
    )
