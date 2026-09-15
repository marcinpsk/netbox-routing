# SPDX-License-Identifier: Apache-2.0

from netbox.api.viewsets import NetBoxModelViewSet

from netbox_routing import filtersets
from netbox_routing.api._serializers.redistribution import *
from netbox_routing.models.redistribution import Redistribution

__all__ = ('RedistributionViewSet',)


class RedistributionViewSet(NetBoxModelViewSet):
    queryset = Redistribution.objects.all()
    serializer_class = RedistributionSerializer
    filterset_class = filtersets.RedistributionFilterSet
