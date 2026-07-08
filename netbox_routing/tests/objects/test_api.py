from ipam.models import Prefix
from utilities.testing import APIViewTestCases

from netbox_routing.models.community import Community, CommunityList
from netbox_routing.models.objects import *

__all__ = (
    'ASPathTestCase',
    'ASPathEntryTestCase',
    'PrefixListTestCase',
    'PrefixListEntryTestCase',
    'RouteMapTestCase',
    'RouteMapEntryTestCase',
    'RouteMapEntrySetCommunityAPITestCase',
)


class ASPathTestCase(APIViewTestCases.APIViewTestCase):
    model = ASPath
    view_namespace = "plugins-api:netbox_routing"
    graphql_base_name = 'aspath'
    brief_fields = [
        'display',
        'id',
        'name',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        cls.aspath = (
            cls.model(
                name='AS Path List 1',
            ),
            cls.model(
                name='AS Path List 2',
            ),
            cls.model(
                name='AS Path List 3',
            ),
        )
        cls.model.objects.bulk_create(cls.aspath)

        cls.create_data = [
            {
                'name': 'AS Path List 4',
            },
            {
                'name': 'AS Path List 5',
            },
        ]


class ASPathEntryTestCase(APIViewTestCases.APIViewTestCase):
    model = ASPathEntry
    view_namespace = "plugins-api:netbox_routing"
    graphql_base_name = 'aspath_entry'
    brief_fields = [
        'action',
        'aspath',
        'display',
        'id',
        'pattern',
        'sequence',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        cls.aspath = (
            ASPath(
                name='AS Path List 1',
            ),
            ASPath(
                name='AS Path List 2',
            ),
        )
        ASPath.objects.bulk_create(cls.aspath)

        cls.aspath_entry = (
            cls.model(
                aspath=cls.aspath[0], action='permit', sequence=1, pattern='^2448$'
            ),
            cls.model(
                aspath=cls.aspath[0], action='permit', sequence=2, pattern='^2448 2447$'
            ),
            cls.model(
                aspath=cls.aspath[1], action='permit', sequence=1, pattern='^.*$'
            ),
        )
        cls.model.objects.bulk_create(cls.aspath_entry)

        cls.create_data = [
            {
                'aspath': cls.aspath[0].pk,
                'action': 'permit',
                'sequence': 3,
                'pattern': '^2448 2448 2448$',
            },
            {
                'aspath': cls.aspath[0].pk,
                'action': 'permit',
                'sequence': 4,
                'pattern': '^2448 2448 2448 2448$',
            },
        ]


class PrefixListTestCase(APIViewTestCases.APIViewTestCase):
    model = PrefixList
    view_namespace = "plugins-api:netbox_routing"
    graphql_base_name = 'prefixlist'
    brief_fields = [
        'display',
        'id',
        'name',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = (
            cls.model(
                name='Prefix List 1',
            ),
            cls.model(
                name='Prefix List 2',
            ),
            cls.model(
                name='Prefix List 3',
            ),
        )
        cls.model.objects.bulk_create(cls.prefix_list)

        cls.create_data = [
            {
                'name': 'Prefix List 4',
            },
            {
                'name': 'Prefix List 5',
            },
        ]


class PrefixListEntryTestCase(APIViewTestCases.APIViewTestCase):
    model = PrefixListEntry
    view_namespace = "plugins-api:netbox_routing"
    graphql_base_name = 'prefixlist_entry'
    brief_fields = [
        'action',
        'assigned_prefix_id',
        'assigned_prefix_type',
        'display',
        'ge',
        'id',
        'le',
        'prefix_list',
        'sequence',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        prefixes = (
            Prefix(prefix='10.0.0.0/24'),
            Prefix(prefix='10.0.1.0/24'),
            Prefix(prefix='10.0.2.0/24'),
            Prefix(prefix='10.0.3.0/24'),
        )
        Prefix.objects.bulk_create(prefixes)

        custom_prefixes = (
            CustomPrefix(prefix='10.0.0.0/24'),
            CustomPrefix(prefix='10.0.4.0/24'),
        )
        CustomPrefix.objects.bulk_create(custom_prefixes)

        cls.prefix_list = (
            PrefixList(
                name='Prefix List 1',
            ),
            PrefixList(
                name='Prefix List 2',
            ),
        )
        PrefixList.objects.bulk_create(cls.prefix_list)

        cls.prefix_list_entry = (
            cls.model(
                prefix_list=cls.prefix_list[0],
                action='permit',
                sequence=1,
                assigned_prefix=prefixes[0],
            ),
            cls.model(
                prefix_list=cls.prefix_list[0],
                action='permit',
                sequence=2,
                assigned_prefix=prefixes[1],
            ),
            cls.model(
                prefix_list=cls.prefix_list[1],
                action='permit',
                sequence=1,
                assigned_prefix=custom_prefixes[0],
            ),
        )
        cls.model.objects.bulk_create(cls.prefix_list_entry)

        cls.create_data = [
            {
                'prefix_list': cls.prefix_list[0].pk,
                'action': 'permit',
                'sequence': 3,
                'assigned_prefix_type': 'ipam.prefix',
                'assigned_prefix_id': prefixes[0].pk,
            },
            {
                'prefix_list': cls.prefix_list[0].pk,
                'action': 'permit',
                'sequence': 4,
                'assigned_prefix_type': 'netbox_routing.customprefix',
                'assigned_prefix_id': custom_prefixes[1].pk,
            },
        ]


class RouteMapTestCase(APIViewTestCases.APIViewTestCase):
    model = RouteMap
    view_namespace = "plugins-api:netbox_routing"
    brief_fields = [
        'display',
        'id',
        'name',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        cls.route_map = (
            cls.model(
                name='Route Map 1',
            ),
            cls.model(
                name='Route Map 2',
            ),
            cls.model(
                name='Route Map 3',
            ),
        )
        cls.model.objects.bulk_create(cls.route_map)

        cls.create_data = [
            {
                'name': 'Route Map 4',
            },
            {
                'name': 'Route Map 5',
            },
        ]


class RouteMapEntryTestCase(APIViewTestCases.APIViewTestCase):
    model = RouteMapEntry
    view_namespace = "plugins-api:netbox_routing"
    brief_fields = [
        'action',
        'display',
        'id',
        'route_map',
        'sequence',
        'url',
    ]

    bulk_update_data = {'description': 'Description'}

    @classmethod
    def setUpTestData(cls):
        cls.route_map = (
            RouteMap(
                name='Route Map 1',
            ),
            RouteMap(
                name='Route Map 2',
            ),
        )
        RouteMap.objects.bulk_create(cls.route_map)

        cls.route_map_entry = (
            cls.model(
                route_map=cls.route_map[0],
                action='permit',
                sequence=1,
                match={'tags': 1},
                set={},
            ),
            cls.model(
                route_map=cls.route_map[0],
                action='permit',
                sequence=2,
                match={'tags': 2},
                set={},
            ),
            cls.model(
                route_map=cls.route_map[1],
                action='permit',
                sequence=1,
                match={'tags': 3},
                set={},
            ),
        )
        cls.model.objects.bulk_create(cls.route_map_entry)

        cls.create_data = [
            {
                'route_map': cls.route_map[0].pk,
                'action': 'permit',
                'sequence': 3,
                'match': {'tags': 4},
            },
            {
                'route_map': cls.route_map[0].pk,
                'action': 'permit',
                'sequence': 4,
                'match': {'tags': 5},
            },
        ]


class RouteMapEntrySetCommunityAPITestCase(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    """API coverage for the writable RouteMapEntrySetCommunity endpoint.

    RouteMapEntrySetCommunity is a plain (non-NetBox) child model, so it is
    composed from the individual API mixins rather than the full
    ``APIViewTestCase`` (no GraphQL / changelog surface).
    """

    model = RouteMapEntrySetCommunity
    view_namespace = "plugins-api:netbox_routing"
    brief_fields = [
        'communities',
        'community_list',
        'id',
        'operation',
        'route_map_entry',
        'url',
    ]
    bulk_update_data = {'operation': 'delete'}
    user_permissions = (
        'netbox_routing.view_routemapentry',
        'netbox_routing.view_communitylist',
        'netbox_routing.view_community',
    )

    @classmethod
    def setUpTestData(cls):
        route_map = RouteMap.objects.create(name='RM 1')
        entry = RouteMapEntry.objects.create(
            route_map=route_map, action='permit', sequence=1
        )
        clist = CommunityList.objects.create(name='CL 1')
        communities = (
            Community.objects.create(community='65000:1', status='active'),
            Community.objects.create(community='65000:2', status='active'),
        )

        objs = (
            RouteMapEntrySetCommunity(
                route_map_entry=entry, operation='add', community_list=clist
            ),
            RouteMapEntrySetCommunity(
                route_map_entry=entry, operation='set', community_list=clist
            ),
            RouteMapEntrySetCommunity(route_map_entry=entry, operation='delete'),
        )
        RouteMapEntrySetCommunity.objects.bulk_create(objs)
        objs[0].communities.set(communities)

        cls.create_data = [
            {
                'route_map_entry': entry.pk,
                'operation': 'add',
                'community_list': clist.pk,
            },
            {
                'route_map_entry': entry.pk,
                'operation': 'set',
                'communities': [communities[0].pk, communities[1].pk],
            },
            {
                'route_map_entry': entry.pk,
                'operation': 'delete',
            },
        ]
