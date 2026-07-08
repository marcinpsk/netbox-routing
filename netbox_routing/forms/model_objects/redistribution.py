# SPDX-License-Identifier: Apache-2.0

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from netbox.forms import PrimaryModelForm
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet, TabbedGroups

from netbox_routing.models.bgp import BGPAddressFamily
from netbox_routing.models.isis import ISISInstance
from netbox_routing.models.objects import RouteMap
from netbox_routing.models.ospf import OSPFInstance
from netbox_routing.models.redistribution import Redistribution

__all__ = ('RedistributionForm',)


class RedistributionForm(PrimaryModelForm):
    """Redistribution editor.

    ``destination`` is a GFK; mirror the fork ``BGPSetting`` idiom of one selector
    per supported destination scope inside TabbedGroups, resolved to the GFK in
    ``clean()``.
    """

    ospf_instance = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        selector=True,
        label=_('OSPF Instance'),
    )
    isis_instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=False,
        selector=True,
        label=_('IS-IS Instance'),
    )
    bgp_address_family = DynamicModelChoiceField(
        queryset=BGPAddressFamily.objects.all(),
        required=False,
        selector=True,
        label=_('BGP Address Family'),
    )
    route_map = DynamicModelChoiceField(
        queryset=RouteMap.objects.all(),
        required=False,
        selector=True,
        label=_('Route Map'),
    )

    fieldsets = (
        FieldSet(
            TabbedGroups(
                FieldSet('ospf_instance', name=_('OSPF')),
                FieldSet('isis_instance', name=_('IS-IS')),
                FieldSet('bgp_address_family', name=_('BGP')),
            ),
            name=_('Destination'),
        ),
        FieldSet('source_protocol', 'source_ref', name=_('Source')),
        FieldSet(
            'route_map',
            'metric',
            'metric_type',
            'description',
            name=_('Attributes'),
        ),
        FieldSet('tags', name=_('Tags')),
    )

    class Meta:
        model = Redistribution
        fields = (
            'ospf_instance',
            'isis_instance',
            'bgp_address_family',
            'source_protocol',
            'source_ref',
            'route_map',
            'metric',
            'metric_type',
            'description',
            'comments',
            'tags',
            'owner',
        )

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        initial = kwargs.get('initial', {}).copy()
        if instance is not None and instance.destination_id:
            destination = instance.destination
            if type(destination) is OSPFInstance:
                initial['ospf_instance'] = destination
            elif type(destination) is ISISInstance:
                initial['isis_instance'] = destination
            elif type(destination) is BGPAddressFamily:
                initial['bgp_address_family'] = destination
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()

        selected_objects = [
            field
            for field in ('ospf_instance', 'isis_instance', 'bgp_address_family')
            if self.cleaned_data.get(field)
        ]
        if len(selected_objects) > 1:
            raise forms.ValidationError(
                {
                    selected_objects[1]: _(
                        'A redistribution can only target a single destination.'
                    )
                }
            )
        elif selected_objects:
            self.instance.destination = self.cleaned_data[selected_objects[0]]
        else:
            raise ValidationError(
                _('A redistribution must specify a destination protocol scope.')
            )
