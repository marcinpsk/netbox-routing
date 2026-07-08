# SPDX-License-Identifier: Apache-2.0

from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels

from netbox_routing.ui.attributes import ContentTypeAttribute

__all__ = ('RedistributionPanel',)


class RedistributionPanel(panels.ObjectAttributesPanel):
    destination_type = ContentTypeAttribute(
        'destination_type', label=_('Destination Type')
    )
    destination = attrs.RelatedObjectAttr(
        'destination', linkify=True, label=_('Destination')
    )
    source_protocol = attrs.ChoiceAttr('source_protocol', label=_('Source Protocol'))
    source_ref = attrs.TextAttr('source_ref', label=_('Source Reference'))
    route_map = attrs.RelatedObjectAttr('route_map', linkify=True, label=_('Route Map'))
    metric = attrs.NumericAttr('metric', label=_('Metric'))
    metric_type = attrs.ChoiceAttr('metric_type', label=_('Metric Type'))
    description = attrs.TextAttr('description', label=_('Description'))
