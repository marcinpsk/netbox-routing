# from django.core.exceptions import ValidationError
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from ipam.models import Prefix
from netbox_routing.models.objects import *

__all__ = (
    'ASPathTestCase',
    'ASPathEntryTestCase',
    'PrefixListTestCase',
    'PrefixListEntryTestCase',
    'RouteMapTestCase',
    'RouteMapEntryTestCase',
)


class ASPathTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def test_community(self):
        name = 'AS Path 1'
        asp = ASPath(
            name=name,
        )
        asp.full_clean()
        asp.save()
        self.assertIsInstance(asp, ASPath)
        self.assertEqual(asp.__str__(), name)

    def test_unique_together(self):

        name = 'AS Path 1'
        asp = ASPath(
            name=name,
        )
        asp.full_clean()
        asp.save()

        asp = ASPath(
            name=name,
        )

        with self.assertRaises(ValidationError):
            asp.full_clean()
        with self.assertRaises(IntegrityError):
            asp.save()


class ASPathEntryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.aspath = ASPath(
            name='AS Path',
        )
        cls.aspath.full_clean()
        cls.aspath.save()

    def test_aspath_entry(self):
        for seq, pattern in (
            (1, '^1$'),
            (2, '^2$'),
            (3, '^3$'),
            (4, '^4$'),
        ):
            aspe = ASPathEntry(
                aspath=self.aspath,
                action='permit',
                sequence=seq,
                pattern=pattern,
            )
            aspe.full_clean()
            aspe.save()
            self.assertIsInstance(aspe, ASPathEntry)
            self.assertEqual(aspe.__str__(), f'{self.aspath} permit {seq}')


class PrefixListTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def test_community(self):
        name = 'Prefix List 1'
        pl = PrefixList(
            name=name,
        )
        pl.full_clean()
        pl.save()
        self.assertIsInstance(pl, PrefixList)
        self.assertEqual(pl.__str__(), name)

    def test_unique_together(self):

        name = 'Prefix List 1'
        pl = PrefixList(
            name=name,
        )
        pl.full_clean()
        pl.save()

        pl = PrefixList(
            name=name,
        )

        with self.assertRaises(ValidationError):
            pl.full_clean()
        with self.assertRaises(IntegrityError):
            pl.save()


class PrefixListEntryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.prefix_list = PrefixList(
            name='Prefix List',
        )
        cls.prefix_list.full_clean()
        cls.prefix_list.save()

    def test_prefix_list_entry(self):
        for seq, pattern in (
            (1, '10.0.1.0/24'),
            (2, '10.0.2.0/24'),
            (3, '10.0.3.0/24'),
            (4, '10.0.4.0/24'),
        ):
            if seq in [
                1,
                3,
            ]:
                prefix = CustomPrefix(prefix=pattern)
            else:
                prefix = Prefix(prefix=pattern)
            prefix.full_clean()
            prefix.save()

            ple = PrefixListEntry(
                prefix_list=self.prefix_list,
                action='permit',
                sequence=seq,
                assigned_prefix=prefix,
            )
            ple.full_clean()
            ple.save()
            self.assertIsInstance(ple, PrefixListEntry)
            self.assertEqual(ple.__str__(), f'{self.prefix_list} permit {seq}')


class RouteMapTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        pass

    def test_community(self):
        name = 'Route Map 1'
        rm = RouteMap(
            name=name,
        )
        rm.full_clean()
        rm.save()
        self.assertIsInstance(rm, RouteMap)
        self.assertEqual(rm.__str__(), name)

    def test_unique_together(self):

        name = 'Route Map 1'
        rm = RouteMap(
            name=name,
        )
        rm.full_clean()
        rm.save()

        rm = RouteMap(
            name=name,
        )

        with self.assertRaises(ValidationError):
            rm.full_clean()
        with self.assertRaises(IntegrityError):
            rm.save()

    def test_default_action(self):
        # Policy-level default-action (vendor default when no entry matches); blank = none.
        rm = RouteMap(name='RM Default', default_action='deny')
        rm.full_clean()
        rm.save()
        rm.refresh_from_db()
        self.assertEqual(rm.default_action, 'deny')

        rm_none = RouteMap(name='RM No Default')
        rm_none.full_clean()
        rm_none.save()
        rm_none.refresh_from_db()
        self.assertIsNone(rm_none.default_action)

    def test_default_action_rejects_unknown(self):
        rm = RouteMap(name='RM Bad Default', default_action='bogus')
        with self.assertRaises(ValidationError):
            rm.full_clean()


class RouteMapEntryTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.route_map = RouteMap(
            name='Route Map',
        )
        cls.route_map.full_clean()
        cls.route_map.save()

    def test_route_map_entry(self):
        for seq, pattern in (
            (1, '10.0.1.0/24'),
            (2, '10.0.2.0/24'),
            (3, '10.0.3.0/24'),
            (4, '10.0.4.0/24'),
        ):
            rme = RouteMapEntry(
                route_map=self.route_map,
                action='permit',
                sequence=seq,
                match={'tags': f'{seq}{seq}{seq}{seq}'},
            )
            rme.full_clean()
            rme.save()
            self.assertIsInstance(rme, RouteMapEntry)
            self.assertEqual(rme.__str__(), f'{self.route_map} permit {seq}')

    def test_vendor_ext(self):
        # Namespaced vendor-extension carrier (successor to the _rpl_/_junos_/_timos_ blobs).
        rme = RouteMapEntry(
            route_map=self.route_map,
            action='permit',
            sequence=10,
            vendor_ext={'timos': {'default_action': True}, 'junos': {'priority': 'high'}},
        )
        rme.full_clean()
        rme.save()
        rme.refresh_from_db()
        self.assertEqual(rme.vendor_ext['timos']['default_action'], True)
        self.assertEqual(rme.vendor_ext['junos']['priority'], 'high')

    def test_set_community_by_ref_and_inline(self):
        # By-reference (community-list + op) AND inline (literal communities) set-actions;
        # one entry can carry several. Replaces the lossy single inline value in set-JSON.
        from netbox_routing.models.community import Community, CommunityList

        cl = CommunityList.objects.create(name='CL-SET')
        c1 = Community.objects.create(community='65000:1')
        rme = RouteMapEntry.objects.create(route_map=self.route_map, action='permit', sequence=20)

        add = RouteMapEntrySetCommunity.objects.create(
            route_map_entry=rme, operation='add', community_list=cl
        )
        inline = RouteMapEntrySetCommunity.objects.create(route_map_entry=rme, operation='set')
        inline.communities.add(c1)

        self.assertEqual(rme.set_communities.count(), 2)
        self.assertEqual(rme.set_communities.get(operation='add').community_list, cl)
        self.assertEqual(list(rme.set_communities.get(operation='set').communities.all()), [c1])
        self.assertEqual(str(add), 'add CL-SET')
        self.assertEqual(str(inline), 'set inline')

    def test_set_community_operation_rejects_unknown(self):
        rme = RouteMapEntry.objects.create(route_map=self.route_map, action='permit', sequence=21)
        obj = RouteMapEntrySetCommunity(route_map_entry=rme, operation='bogus')
        with self.assertRaises(ValidationError):
            obj.full_clean()

    def test_match_afi(self):
        # Per-entry address-family match (Junos from-family / Nokia from-family), multi-valued.
        rme = RouteMapEntry(
            route_map=self.route_map,
            action='permit',
            sequence=30,
            match_afi=['ipv4', 'vpn-ipv4'],
        )
        rme.full_clean()
        rme.save()
        rme.refresh_from_db()
        self.assertEqual(rme.match_afi, ['ipv4', 'vpn-ipv4'])

    def test_match_afi_rejects_unknown(self):
        rme = RouteMapEntry(
            route_map=self.route_map, action='permit', sequence=31, match_afi=['bogus']
        )
        with self.assertRaises(ValidationError):
            rme.full_clean()

    def test_call_and_apply_policy(self):
        # A policy used as a match subroutine (Junos from-policy / IOS-XR apply) and as a
        # tail-call; PROTECT keeps a referenced policy from being deleted out from under it.
        from django.db.models import ProtectedError

        sub = RouteMap.objects.create(name='SUB-POLICY')
        rme = RouteMapEntry(
            route_map=self.route_map, action='permit', sequence=40, call_policy=sub, apply_policy=sub
        )
        rme.full_clean()
        rme.save()
        rme.refresh_from_db()
        self.assertEqual(rme.call_policy, sub)
        self.assertEqual(rme.apply_policy, sub)
        with self.assertRaises(ProtectedError):
            sub.delete()

    def test_match_condition_valid_tree(self):
        rme = RouteMapEntry(
            route_map=self.route_map,
            action='permit',
            sequence=41,
            match_condition={
                'op': 'or',
                'args': [
                    {'match': 'community', 'ref': 'CL-A'},
                    {'op': 'not', 'args': [{'match': 'aspath', 'ref': 'AP-X'}]},
                ],
            },
        )
        rme.full_clean()
        rme.save()
        rme.refresh_from_db()
        self.assertEqual(rme.match_condition['op'], 'or')

    def test_match_condition_rejects_malformed(self):
        for bad in (
            {'op': 'xor', 'args': [{'match': 'community'}]},  # unknown op
            {'op': 'and', 'args': []},  # empty args
            {'op': 'not', 'args': [{'match': 'x'}, {'match': 'y'}]},  # not with 2 args
            {'foo': 'bar'},  # neither op nor match
        ):
            rme = RouteMapEntry(
                route_map=self.route_map, action='permit', sequence=42, match_condition=bad
            )
            with self.assertRaises(ValidationError):
                rme.full_clean()
