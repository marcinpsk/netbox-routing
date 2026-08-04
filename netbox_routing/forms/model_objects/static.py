from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

from dcim.models import Device
from ipam.models import VRF
from netbox.forms import PrimaryModelForm
from netbox_routing.helpers.static import (
    interface_only_conversion_errors,
    shared_device_triple_errors,
    stored_route,
)
from netbox_routing.models import StaticRoute
from utilities.forms.fields import (
    DynamicModelChoiceField,
    DynamicModelMultipleChoiceField,
)
from utilities.forms.rendering import FieldSet


class StaticRouteForm(PrimaryModelForm):
    devices = DynamicModelMultipleChoiceField(
        queryset=Device.objects.all(),
        label=_('Devices'),
    )
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        label=_('VRF'),
    )

    fieldsets = (
        FieldSet(
            'devices',
            'vrf',
        ),
        FieldSet(
            'prefix',
            'next_hop',
            'interface_next_hop',
            'metric',
            name=_('Route'),
        ),
        FieldSet(
            'name',
            'description',
            'tag',
            'permanent',
            name=_('Metadata'),
        ),
        FieldSet(
            'tags',
            name=_('Tags'),
        ),
    )

    class Meta:
        model = StaticRoute
        fields = (
            'devices',
            'vrf',
            'prefix',
            'next_hop',
            'interface_next_hop',
            'name',
            'metric',
            'permanent',
            'tag',
            'description',
            'comments',
            'tags',
            'owner',
        )

    def __init__(self, data=None, instance=None, *args, **kwargs):
        super().__init__(*args, data=data, instance=instance, **kwargs)

        if self.instance and self.instance.pk is not None:
            self.fields['devices'].initial = self.instance.devices.all().values_list(
                'id', flat=True
            )

    def clean(self):
        # NetBox's PrimaryModelForm.clean() returns None, so read the attribute.
        super().clean()
        cleaned_data = self.cleaned_data

        stored = stored_route(self.instance)
        errors = {}
        errors.update(
            shared_device_triple_errors(
                stored,
                cleaned_data.get('vrf'),
                cleaned_data.get('prefix'),
                cleaned_data.get('next_hop'),
                cleaned_data.get('devices'),
            )
        )
        errors.update(
            interface_only_conversion_errors(
                stored,
                cleaned_data.get('next_hop'),
                cleaned_data.get('interface_next_hop'),
            )
        )
        if errors:
            raise ValidationError(errors)

        return cleaned_data

    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        instance.devices.set(self.cleaned_data['devices'])
        return instance
