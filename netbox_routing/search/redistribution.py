# SPDX-License-Identifier: Apache-2.0

from netbox.search import SearchIndex, register_search

from netbox_routing.models.redistribution import Redistribution

__all__ = ('RedistributionIndex',)


@register_search
class RedistributionIndex(SearchIndex):
    model = Redistribution
    fields = (
        ('source_protocol', 100),
        ('source_ref', 200),
        ('description', 4000),
        ('comments', 5000),
    )
    display_attrs = ('source_protocol', 'source_ref')
