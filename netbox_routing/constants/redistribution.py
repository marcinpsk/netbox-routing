# SPDX-License-Identifier: Apache-2.0

from functools import reduce
from operator import or_

from django.db.models import Q

__all__ = (
    'REDISTRIBUTION_DESTINATION_MODEL_KEYS',
    'REDISTRIBUTION_DESTINATION_MODELS',
)


# Single source of truth for the (app_label, model) identities allowed as a
# Redistribution destination. Both ``Redistribution.ALLOWED_DESTINATION_MODELS``
# (the model-level scope guard) and the GFK content-type choices below derive from
# this, so a new destination type can't be added to one and silently missed by the
# other.
REDISTRIBUTION_DESTINATION_MODEL_KEYS = (
    ('netbox_routing', 'ospfinstance'),
    ('netbox_routing', 'isisinstance'),
    ('netbox_routing', 'bgpaddressfamily'),
)

# Content-type choices for the destination GFK (ContentTypeField queryset / form
# selectors). Derived from REDISTRIBUTION_DESTINATION_MODEL_KEYS above.
REDISTRIBUTION_DESTINATION_MODELS = reduce(
    or_,
    (
        Q(app_label=app_label, model=model)
        for app_label, model in REDISTRIBUTION_DESTINATION_MODEL_KEYS
    ),
)
