# SPDX-License-Identifier: Apache-2.0
"""Redistribution model for netbox-routing (M20).

One row = one `redistribute <source>` statement configured on a destination
routing protocol scope (OSPFInstance, ISISInstance, or BGPAddressFamily).

Design: GFK destination (mirrors fork BGPSetting idiom), lenient source
identification (source_protocol enum + nullable source_ref string).
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from netbox.models import PrimaryModel

from netbox_routing.constants.redistribution import (
    REDISTRIBUTION_DESTINATION_MODEL_KEYS,
)

__all__ = ('Redistribution',)


class SourceProtocolChoices(models.TextChoices):
    CONNECTED = 'connected', _('Connected')
    STATIC = 'static', _('Static')
    OSPF = 'ospf', _('OSPF')
    ISIS = 'isis', _('IS-IS')
    BGP = 'bgp', _('BGP')
    EIGRP = 'eigrp', _('EIGRP')
    RIP = 'rip', _('RIP')


class MetricTypeChoices(models.TextChoices):
    OSPF_TYPE1 = '1', _('OSPF Type-1')
    OSPF_TYPE2 = '2', _('OSPF Type-2')
    ISIS_INTERNAL = 'internal', _('IS-IS Internal')
    ISIS_EXTERNAL = 'external', _('IS-IS External')


# Metric types are protocol-specific; map each destination scope model to the
# metric_type values it accepts. Keyed by the full (app_label, model) content-type
# identity — ContentType.model is only unique per app, so a same-named model from
# another app must not be able to satisfy this mapping. A destination not listed
# here (e.g. BGP) does not support a metric_type at all.
METRIC_TYPES_BY_DESTINATION = {
    ('netbox_routing', 'ospfinstance'): frozenset(
        (MetricTypeChoices.OSPF_TYPE1, MetricTypeChoices.OSPF_TYPE2)
    ),
    ('netbox_routing', 'isisinstance'): frozenset(
        (MetricTypeChoices.ISIS_INTERNAL, MetricTypeChoices.ISIS_EXTERNAL)
    ),
}

# Destination scope is a GFK, but only these protocol-scope models are valid
# targets (BGP destinations carry no metric_type, hence absent above). Keyed by
# full (app_label, model) so an unrelated app's like-named model can't slip through.
# Derived from the single source of truth in constants/redistribution.py — the same
# keys back the GFK's content-type choices, so the scope guard and the UI/API picker
# can't drift.
ALLOWED_DESTINATION_MODELS = frozenset(REDISTRIBUTION_DESTINATION_MODEL_KEYS)


class Redistribution(PrimaryModel):
    """Redistribute statement from a source protocol into a destination protocol scope.

    ``destination`` is a GenericForeignKey to the destination scope object:
    - OSPFInstance for OSPF destinations
    - ISISInstance for IS-IS destinations
    - BGPAddressFamily for BGP destinations
    """

    destination_type = models.ForeignKey(
        verbose_name=_('Destination Type'),
        to=ContentType,
        on_delete=models.CASCADE,
        related_name='+',
        blank=False,
        null=False,
    )
    destination_id = models.PositiveBigIntegerField(
        verbose_name=_('Destination ID'),
        blank=False,
        null=False,
    )
    destination = GenericForeignKey(
        ct_field='destination_type',
        fk_field='destination_id',
    )
    source_protocol = models.CharField(
        verbose_name=_('Source Protocol'),
        max_length=16,
        choices=SourceProtocolChoices,
    )
    source_ref = models.CharField(
        verbose_name=_('Source Reference'),
        help_text=_(
            'Process ID, area tag, or ASN identifying the source instance. Leave blank for connected/static.'
        ),
        max_length=64,
        blank=True,
        default='',
    )
    route_map = models.ForeignKey(
        verbose_name=_('Route Map'),
        to='netbox_routing.RouteMap',
        on_delete=models.SET_NULL,
        related_name='redistribution_entries',
        blank=True,
        null=True,
    )
    metric = models.PositiveIntegerField(
        verbose_name=_('Metric'),
        blank=True,
        null=True,
    )
    metric_type = models.CharField(
        verbose_name=_('Metric Type'),
        max_length=16,
        choices=MetricTypeChoices,
        blank=True,
        default='',
    )

    clone_fields = (
        'destination_type',
        'destination_id',
        'source_protocol',
        'source_ref',
        'route_map',
    )
    prerequisite_models = ()

    class Meta:
        ordering = [
            'destination_type',
            'destination_id',
            'source_protocol',
            'source_ref',
        ]
        verbose_name = 'Redistribution'
        verbose_name_plural = 'Redistributions'
        constraints = [
            models.UniqueConstraint(
                fields=(
                    'destination_type',
                    'destination_id',
                    'source_protocol',
                    'source_ref',
                ),
                name='netbox_routing_redistribution_unique_destination_source',
            ),
        ]

    def clean(self):
        super().clean()

        model = None
        destination_key = None
        if self.destination_type_id:
            model = self.destination_type.model_class()
            # Full content-type identity: model name alone is not globally unique.
            destination_key = (
                self.destination_type.app_label,
                self.destination_type.model,
            )

            # Destination must be one of the supported protocol-scope models.
            if destination_key not in ALLOWED_DESTINATION_MODELS:
                label = (
                    model._meta.verbose_name
                    if model is not None
                    else self.destination_type
                )
                raise ValidationError(
                    {
                        'destination_type': _(
                            '%(model)s is not a valid redistribution destination.'
                        )
                        % {'model': label}
                    }
                )

        # metric_type is protocol-specific: constrain it to the values valid for
        # the selected destination scope so e.g. an IS-IS metric_type can't be
        # saved against an OSPF destination.
        if self.metric_type and self.destination_type_id:
            allowed = METRIC_TYPES_BY_DESTINATION.get(destination_key, frozenset())
            if self.metric_type not in allowed:
                destination_label = (
                    model._meta.verbose_name if model is not None else _('destination')
                )
                raise ValidationError(
                    {
                        'metric_type': _(
                            'Metric type "%(value)s" is not valid for a %(destination)s destination.'
                        )
                        % {
                            'value': self.metric_type,
                            'destination': destination_label,
                        }
                    }
                )

    def __str__(self):
        src = f'{self.source_protocol}'
        if self.source_ref:
            src += f' {self.source_ref}'
        return f'{self.destination} ← {src}'

    def get_absolute_url(self):
        return reverse('plugins:netbox_routing:redistribution', args=[self.pk])
