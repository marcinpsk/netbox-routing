from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from ipam.models import Role

from netbox_routing.choices import ActionChoices, CommunityKindChoices
from netbox_routing.models.community import *

__all__ = (
    'CommunityTestCase',
    'CommunityKindTestCase',
    'CommunityListTestCase',
    'CommunityListEntryTestCase',
)


class CommunityTestCase(TestCase):
    def setUp(self):
        Role.objects.create(name='Test Role')

    def test_community(self):
        role = Role.objects.get(name='Test Role')
        community_value = '64512'
        community = Community(
            community=community_value,
            status='active',
            role=role,
        )
        community.full_clean()
        community.save()
        self.assertIsInstance(community, Community)
        self.assertEqual(community.__str__(), community_value)

        community_value = '64512:64512'
        community = Community(
            community=community_value,
            status='active',
            role=role,
        )
        community.full_clean()
        community.save()
        self.assertIsInstance(community, Community)
        self.assertEqual(community.__str__(), community_value)

        community_value = '64512:64512:64512'
        community = Community(
            community=community_value,
            status='active',
            role=role,
        )
        community.full_clean()
        community.save()
        self.assertIsInstance(community, Community)
        self.assertEqual(community.__str__(), community_value)

    def test_universal_forms_accepted(self):
        """The single universal field stores every device form verbatim — numeric, well-known
        keyword, typed extended, RFC 8092 large (prefixed and bare), and match-only regex —
        with NO part cap (the kind is derived by parsing, not constrained by the validator)."""
        role = Role.objects.get(name='Test Role')
        for value in (
            '1111:1234',  # standard
            'target:1111:1234',  # extended (keyword)
            'large:1111:6370:1234',  # large (prefixed)
            '64512:64512:64512:64512',  # 4 parts — no longer rejected (cap dropped)
            'no-export',  # well-known keyword
            'color:0:128',  # extended
            '1111:*',  # regex
            '1111:.*',  # regex
            '1111:1113.',  # dotted regex
        ):
            community = Community(community=value, status='active', role=role)
            community.full_clean()  # must not raise
            community.save()
            self.assertEqual(community.community, value)

    def test_whitespace_rejected(self):
        """The validator still rejects whitespace — the one thing no device member contains."""
        role = Role.objects.get(name='Test Role')
        for value in ('not valid', '1111: 100', ' '):
            bad = Community(community=value, status='active', role=role)
            with self.assertRaises(ValidationError):
                bad.full_clean()

    def test_str_with_name(self):
        role = Role.objects.get(name='Test Role')
        community = Community(
            name='blackhole',
            community='65000:666',
            status='active',
            role=role,
        )
        community.full_clean()
        community.save()
        self.assertEqual(str(community), 'blackhole (65000:666)')

    def test_str_without_name(self):
        role = Role.objects.get(name='Test Role')
        community = Community(
            community='65000:100',
            status='active',
            role=role,
        )
        community.full_clean()
        community.save()
        self.assertEqual(community.name, '')
        self.assertEqual(str(community), '65000:100')

    def test_unique_together(self):

        role = Role.objects.get(name='Test Role')
        community_value = '64512:64512:64512'
        community = Community(
            community=community_value,
            status='active',
            role=role,
        )
        community.full_clean()
        community.save()

        community = Community(
            community=community_value,
            status='active',
            role=role,
        )

        with self.assertRaises(ValidationError):
            community.full_clean()
        with self.assertRaises(IntegrityError):
            community.save()


class CommunityKindTestCase(TestCase):
    """The kind is derived purely from the community text (no stored column)."""

    # The 9 cnad-test members and their expected derived kinds (the live-verify target).
    CNAD_TEST = [
        ('1111:1234', CommunityKindChoices.KIND_STANDARD),
        ('target:1111:1234', CommunityKindChoices.KIND_EXTENDED),
        ('large:1111:6370:1234', CommunityKindChoices.KIND_LARGE),
        ('no-export', CommunityKindChoices.KIND_STANDARD),
        ('no-advertise', CommunityKindChoices.KIND_STANDARD),
        ('color:0:128', CommunityKindChoices.KIND_EXTENDED),
        ('1111:1.3.', CommunityKindChoices.KIND_STANDARD),  # 2-part regex -> standard
        ('1111:*', CommunityKindChoices.KIND_STANDARD),  # 2-part regex -> standard
        ('color:0:12.', CommunityKindChoices.KIND_EXTENDED),  # regex, ext keyword
    ]

    def test_cnad_test_member_kinds(self):
        for value, expected in self.CNAD_TEST:
            with self.subTest(value=value):
                self.assertEqual(community_kind(value), expected)
                self.assertEqual(Community(community=value).kind, expected)

    def test_bare_three_part_is_large(self):
        # A bare a:b:c (no keyword) is the Cisco large-community form.
        self.assertEqual(community_kind('1111:6370:1234'), CommunityKindChoices.KIND_LARGE)

    def test_ext_prefix_aliases(self):
        for value in ('rt:1:2', 'route-target:1:2', 'origin:1:2', 'soo:1:2', 'bandwidth:1:2'):
            with self.subTest(value=value):
                self.assertEqual(community_kind(value), CommunityKindChoices.KIND_EXTENDED)

    def test_match_keyword(self):
        self.assertEqual(community_match_keyword('1111:1234'), 'community')
        self.assertEqual(community_match_keyword('target:1111:1234'), 'extcommunity')
        self.assertEqual(community_match_keyword('large:1111:6370:1234'), 'large-community')
        self.assertEqual(Community(community='target:1:2').match_keyword, 'extcommunity')


class CommunityListTestCase(TestCase):
    def setUp(self):
        pass

    def test_community_list(self):
        cl = CommunityList(
            name='Test Community List',
        )
        cl.full_clean()
        cl.save()

    def test_community_list_unique(self):
        cl = CommunityList(
            name='Test Community List',
        )
        cl.full_clean()
        cl.save()

        cl = CommunityList(
            name='Test Community List',
        )
        with self.assertRaises(ValidationError):
            cl.full_clean()
        with self.assertRaises(IntegrityError):
            cl.save()


class CommunityListEntryTestCase(TestCase):
    def setUp(self):
        role = Role.objects.create(name='Test Role')
        self.communities = (
            Community(
                community='64512',
                status='active',
                role=role,
            ),
            Community(
                community='64513',
                status='active',
                role=role,
            ),
            Community(
                community='64514',
                status='active',
                role=role,
            ),
            Community(
                community='64515',
                status='active',
                role=role,
            ),
            Community(
                community='64516',
                status='active',
                role=role,
            ),
        )
        Community.objects.bulk_create(self.communities)

        self.cl = CommunityList(
            name='Test Community List',
        )
        self.cl.full_clean()
        self.cl.save()

    def test_community_list_entry(self):
        for community in self.communities:
            cle = CommunityListEntry(
                community_list=self.cl, action=ActionChoices.PERMIT, community=community
            )
            cle.full_clean()
            cle.save()
