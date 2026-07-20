from netbox_routing.tests.eigrp.test_views import *
from netbox_routing.tests.isis.test_views import *
from netbox_routing.tests.ospf.test_views import *
from netbox_routing.tests.static.test_views import *
from netbox_routing.tests.redistribution.test_views import *

__all__ = (
    'StaticRouteTestCase',
    'RedistributionViewTestCase',
    'OSPFInstanceTestCase',
    'OSPFAreaTestCase',
    'OSPFInterfaceTestCase',
    'ISISInstanceViewTestCase',
    'ISISInterfaceViewTestCase',
    'ISISViewExportsTestCase',
    # 'EIGRPRouterTestCase',
    # 'EIGRPAddressFamilyTestCase',
    # 'EIGRPNetworkTestCase',
    # 'EIGRPInterfaceTestCase',
)
