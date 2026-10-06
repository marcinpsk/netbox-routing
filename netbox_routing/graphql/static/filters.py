import strawberry_django
from strawberry_django import BaseFilterLookup, StrFilterLookup

from netbox.graphql.filters import PrimaryModelFilter
from netbox_routing import models
from netbox_routing.graphql.filter_mixins import VRFMixin, DeviceMixin

__all__ = ('StaticRouteFilter',)


@strawberry_django.filter(models.StaticRoute, lookups=True)
class StaticRouteFilter(VRFMixin, DeviceMixin, PrimaryModelFilter):
    prefix: StrFilterLookup | None = strawberry_django.filter_field()
    # next_hop is a custom IPAddressField; expose only exact/in/is_null (BaseFilterLookup).
    # StrFilterLookup's i_ends_with is meaningless on an IP field and yields an empty
    # expected set, which NetBox 4.6.3+'s test_graphql_filter_objects rejects.
    next_hop: BaseFilterLookup[str] | None = strawberry_django.filter_field()
