from django.contrib.auth import get_user_model
from django.test import TestCase

from netbox_routing.models.community import Community, CommunityList
from netbox_routing.models.objects import (
    ASPath,
    RouteMap,
    RouteMapEntry,
    RouteMapEntrySetCommunity,
)


class RouteMapStructuredDetailTestCase(TestCase):
    """The route-map detail panels surface the M17 P1 structured fields (read-only).

    Renders the REAL detail views (panel layout + templates) against real objects so a
    broken accessor — which renders blank rather than erroring — is caught. Red-first: the
    structured fields are not on the pre-P2 panels, and match_aspath used a non-existent
    accessor ('match_as_path_list') so AS-path matches rendered blank.
    """

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_superuser(
            username='rmdetail', password='pw', email='rmdetail@example.com'
        )
        cls.sub_policy = RouteMap.objects.create(name='SUB-POL')
        cls.route_map = RouteMap.objects.create(name='RM-DETAIL', default_action='deny')
        cls.aspath = ASPath.objects.create(name='AP-DETAIL')
        cls.community_list = CommunityList.objects.create(name='CL-SET')
        Community.objects.create(community='65000:1')

        cls.entry = RouteMapEntry.objects.create(
            route_map=cls.route_map,
            action='permit',
            sequence=10,
            match_afi=['ipv4', 'vpn-ipv4'],
            call_policy=cls.sub_policy,
            apply_policy=cls.sub_policy,
            match_condition={
                'op': 'or',
                'args': [{'match': 'community', 'ref': 'CL-A'}],
            },
            vendor_ext={'junos': {'priority': 'high'}},
        )
        cls.entry.match_aspath.add(cls.aspath)
        RouteMapEntrySetCommunity.objects.create(
            route_map_entry=cls.entry,
            operation='add',
            community_list=cls.community_list,
        )

    def setUp(self):
        self.client.force_login(self.user)

    def test_route_map_entry_detail_renders_structured_fields(self):
        response = self.client.get(self.entry.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('ipv4, vpn-ipv4', content)  # match_afi_display
        self.assertIn(
            'add CL-SET', content
        )  # set_communities (RouteMapEntrySetCommunity __str__)
        self.assertIn('SUB-POL', content)  # call_policy / apply_policy linkified
        self.assertIn('AP-DETAIL', content)  # match_aspath now resolves (accessor fix)
        self.assertIn('Match Condition', content)  # match_condition JSON panel
        self.assertIn('Vendor Extensions', content)  # vendor_ext JSON panel

    def test_route_map_detail_renders_default_action(self):
        response = self.client.get(self.route_map.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn('Default Action', content)  # panel row label
        self.assertIn('Deny', content)  # default_action choice display
