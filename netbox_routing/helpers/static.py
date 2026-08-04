# SPDX-License-Identifier: Apache-2.0

from django.utils.translation import gettext as _

__all__ = (
    'interface_only_conversion_errors',
    'shared_device_triple_errors',
    'stored_route',
    'triple_key',
)


def _blank(value):
    """Empty in the "no value stored" sense.

    ``bool()`` is not usable here: ``netaddr.IPAddress('0.0.0.0')`` is falsy, so reading a
    next hop for truth silently treats a real one as absent.
    """
    return value is None or value == ''


def _device_ids(devices):
    """Normalise a pending device assignment (queryset, list of models, or list of pks)."""
    return [getattr(device, 'pk', device) for device in devices or ()]


def triple_key(vrf, prefix, next_hop):
    """The route's identity grain, comparable across model instances and raw values."""
    return (
        getattr(vrf, 'pk', vrf),
        '' if _blank(prefix) else str(prefix),
        '' if _blank(next_hop) else str(next_hop),
    )


def stored_route(instance):
    """The route as persisted, never the pending state.

    NetBox's ValidatedModelSerializer.validate() assigns the incoming values onto the
    serializer's instance before running full_clean(), so by the time a refusal runs the
    in-memory object is already the *post*-edit row. The refusals compare against the
    pre-edit one, so read it back rather than trusting the object handed in.
    """
    from netbox_routing.models import StaticRoute

    if instance is None or not instance.pk:
        return None
    return StaticRoute.objects.filter(pk=instance.pk).first()


def _devices_this_write_lands_on(stored, vrf, prefix, next_hop, device_ids):
    """The devices this write newly puts this triple on — the only ones to check.

    Upstream deliberately dropped the uniqueness constraint, so duplicate triples already
    exist in the wild.  Checking a device the route already held on a triple it already
    had would rediscover such a duplicate and refuse a rename, a metric change or the
    addition of an unrelated device — a fourth refusal rather than one of the three.
    """
    if stored is None:
        return device_ids
    if triple_key(vrf, prefix, next_hop) != triple_key(
        stored.vrf_id, stored.prefix, stored.next_hop
    ):
        # A new triple lands on every device the route is assigned to.
        return device_ids
    held = set(stored.devices.values_list('pk', flat=True))
    return [device_id for device_id in device_ids if device_id not in held]


def shared_device_triple_errors(stored, vrf, prefix, next_hop, devices):
    """Refuse a (vrf, prefix, next_hop) already live on a device this route is assigned to.

    ``stored`` is the persisted row (:func:`stored_route`) or None on create; the other
    arguments are the *pending* state — the form's ``cleaned_data`` or the serializer's
    ``validated_data`` — because the M2M is written after the row is saved and is
    therefore invisible to ``Model.clean()``.  Covers both the second route with an
    identical triple and the edit that lands one object on another object's triple: the
    stored row excludes itself, so only a foreign match refuses.
    """
    from netbox_routing.models import StaticRoute

    device_ids = _device_ids(devices)
    if _blank(prefix) or not device_ids:
        return {}
    landing_ids = _devices_this_write_lands_on(
        stored, vrf, prefix, next_hop, device_ids
    )
    if not landing_ids:
        return {}

    clashes = StaticRoute.objects.filter(
        vrf=vrf, prefix=prefix, next_hop=next_hop, devices__in=landing_ids
    ).distinct()
    if stored is not None:
        clashes = clashes.exclude(pk=stored.pk)
    clash = clashes.first()
    if clash is None:
        return {}

    shared = sorted(str(device) for device in clash.devices.filter(pk__in=landing_ids))
    return {
        'prefix': _(
            'A static route for %(prefix)s in %(vrf)s via %(next_hop)s already exists '
            'on %(devices)s (%(clash)s). A device cannot hold the same route twice.'
        )
        % {
            'prefix': prefix,
            'vrf': vrf if vrf is not None else _('the global routing table'),
            'next_hop': _('no IP next hop') if _blank(next_hop) else next_hop,
            'devices': ', '.join(shared),
            'clash': clash,
        }
    }


def interface_only_conversion_errors(stored, next_hop, interface_next_hop):
    """Refuse converting an NSO-managed route to an interface-only next hop.

    ``nso_states`` is netbox_nso_plugin's reverse accessor and simply does not exist when
    that plugin is not installed — then there is no NSO management to protect and nothing
    to refuse.  Interface-only next hops carry no intent through NSO yet, so the
    conversion would silently drop the route from what NSO is told to configure.
    """
    if stored is None:
        return {}
    if not _blank(next_hop) or _blank(interface_next_hop) or _blank(stored.next_hop):
        return {}

    states = getattr(stored, 'nso_states', None)
    if states is None or not states.exists():
        return {}

    return {
        'interface_next_hop': _(
            'This route is managed by NSO. An interface next hop cannot be configured '
            'through NSO yet, so its IP next hop cannot be removed.'
        )
    }
