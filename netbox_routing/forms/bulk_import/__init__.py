from .community import *
from .eigrp import *
from .isis import *
from .ospf import *
from .static import *

__all__ = (
    # Community
    'CommunityImportForm',
    'CommunityListImportForm',
    'CommunityListEntryImportForm',
    # Extended Community
    # Large Community
    # EIGRP
    'EIGRPRouterImportForm',
    'EIGRPAddressFamilyImportForm',
    'EIGRPNetworkImportForm',
    'EIGRPInterfaceImportForm',
    # IS-IS
    'ISISInstanceImportForm',
    'ISISInterfaceImportForm',
    'ISISSettingImportForm',
    'ISISLevelImportForm',
    'ISISInterfaceLevelImportForm',
    'ISISSegmentRoutingImportForm',
    'ISISFlexAlgoImportForm',
    # OSPF
    'OSPFInstanceImportForm',
    'OSPFAreaImportForm',
    'OSPFInterfaceImportForm',
    # Static
    'StaticRouteImportForm',
)
