from netbox_routing.tests.eigrp.test_filtersets import *
from netbox_routing.tests.isis.test_filtersets import *
from netbox_routing.tests.ospf.test_filtersets import *
from netbox_routing.tests.static.test_filtersets import *
from netbox_routing.tests.redistribution.test_filtersets import *

__all__ = (
    'StaticRouteTestCase',
    'RedistributionFilterSetTestCase',
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
    'ISISInstanceFilterSetTestCase',
    'ISISInterfaceFilterSetTestCase',
    'ISISSettingFilterSetTestCase',
    'ISISSRv6LocatorFilterSetTestCase',
    'EIGRPRouterTestCase',
    'EIGRPAddressFamilyTestCase',
    'EIGRPNetworkTestCase',
    'EIGRPInterfaceTestCase',
)
