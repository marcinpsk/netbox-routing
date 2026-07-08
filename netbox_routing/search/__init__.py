from .bgp import *
from .community import *
from .eigrp import EIGRPRouterIndex, EIGRPAddressFamilyIndex
from .isis import (
    ISISFlexAlgoIndex,
    ISISInstanceIndex,
    ISISInterfaceIndex,
    ISISInterfaceLevelIndex,
    ISISLevelIndex,
    ISISPrefixSIDIndex,
    ISISSegmentRoutingIndex,
    ISISSettingIndex,
    ISISSRv6LocatorIndex,
)
from .objects import *
from .ospf import OSPFInstanceIndex, OSPFAreaIndex
from .static import StaticRouteIndex

__all__ = (
    'ASPathIndex',
    'ASPathEntryIndex',
    'BGPRouterIndex',
    'BGPScopeIndex',
    'BGPAddressFamilyIndex',
    'BGPPeerIndex',
    'BGPPeerAddressFamilyIndex',
    'BGPPeerTemplateIndex',
    'BGPPolicyTemplateIndex',
    'BGPSessionTemplateIndex',
    'CommunityIndex',
    'CommunityListIndex',
    'CommunityListEntryIndex',
    'EIGRPRouterIndex',
    'EIGRPAddressFamilyIndex',
    'ISISFlexAlgoIndex',
    'ISISInstanceIndex',
    'ISISInterfaceIndex',
    'ISISInterfaceLevelIndex',
    'ISISLevelIndex',
    'ISISPrefixSIDIndex',
    'ISISSegmentRoutingIndex',
    'ISISSettingIndex',
    'ISISSRv6LocatorIndex',
    'OSPFInstanceIndex',
    'OSPFAreaIndex',
    'PrefixListIndex',
    'PrefixListEntryIndex',
    'RouteMapIndex',
    'RouteMapEntryIndex',
    'StaticRouteIndex',
)
