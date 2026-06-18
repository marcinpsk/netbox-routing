from .bgp import *
from .community import *
from .eigrp import EIGRPRouterIndex, EIGRPAddressFamilyIndex
from .isis import ISISInstanceIndex, ISISInterfaceIndex
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
    'ISISInstanceIndex',
    'ISISInterfaceIndex',
    'OSPFInstanceIndex',
    'OSPFAreaIndex',
    'PrefixListIndex',
    'PrefixListEntryIndex',
    'RouteMapIndex',
    'RouteMapEntryIndex',
    'StaticRouteIndex',
)
