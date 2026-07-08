# SPDX-License-Identifier: Apache-2.0

from django.db.models import Q

__all__ = ('REDISTRIBUTION_DESTINATION_MODELS',)


# Content-type choices for a Redistribution destination GFK. Kept in sync with
# ``Redistribution.ALLOWED_DESTINATION_MODELS`` (the model-level scope guard).
REDISTRIBUTION_DESTINATION_MODELS = Q(
    Q(app_label='netbox_routing', model='ospfinstance')
    | Q(app_label='netbox_routing', model='isisinstance')
    | Q(app_label='netbox_routing', model='bgpaddressfamily')
)
