from django.core.validators import RegexValidator
from django.db import models
from django.utils.translation import gettext as _

from netbox.models import PrimaryModel

from netbox_routing.choices import (
    ActionChoices,
    CommunityKindChoices,
    CommunityStatusChoices,
)

__all__ = (
    'CommunityList',
    'Community',
    'CommunityListEntry',
    'community_kind',
    'community_match_keyword',
)


# Well-known standard communities (RFC 1997 + common aliases), stored verbatim.
COMMUNITY_WELL_KNOWN = frozenset(
    {
        'no-export',
        'no-advertise',
        'no-export-subconfed',
        'local-as',
        'internet',
        'graceful-shutdown',
    }
)

# Leading keyword (before the first colon) that marks an extended community.
COMMUNITY_EXT_PREFIXES = frozenset(
    {
        'target',
        'rt',
        'route-target',
        'origin',
        'soo',
        'route-origin',
        'color',
        'bandwidth',
        'encapsulation',
    }
)

# Device match-clause keyword per derived kind.
COMMUNITY_MATCH_KEYWORD = {
    CommunityKindChoices.KIND_STANDARD: 'community',
    CommunityKindChoices.KIND_EXTENDED: 'extcommunity',
    CommunityKindChoices.KIND_LARGE: 'large-community',
}


def community_kind(value):
    """Derive a Community's kind (standard/extended/large) from its text alone.

    The member string is stored verbatim — there is no kind column. We parse it
    the way a device does: a ``large:`` prefix is a large community; a type-keyword
    prefix (target:/origin:/color:/…) is extended; a well-known keyword is standard;
    otherwise a bare three-part value (GA:L1:L2, the Cisco large-community form) is
    large and anything else (2-part ``ASN:value`` or a regex/wildcard) is standard.
    """
    v = (value or '').strip()
    head = v.split(':', 1)[0].lower()
    if head == 'large':
        return CommunityKindChoices.KIND_LARGE
    if head in COMMUNITY_EXT_PREFIXES:
        return CommunityKindChoices.KIND_EXTENDED
    if v.lower() in COMMUNITY_WELL_KNOWN:
        return CommunityKindChoices.KIND_STANDARD
    # bare three-part (a:b:c) is a Cisco large community; 2-part / regex is standard
    return (
        CommunityKindChoices.KIND_LARGE
        if v.count(':') >= 2
        else CommunityKindChoices.KIND_STANDARD
    )


def community_match_keyword(value):
    """Device route-map MATCH keyword for the community's derived kind."""
    return COMMUNITY_MATCH_KEYWORD[community_kind(value)]


class CommunityList(PrimaryModel):
    name = models.CharField(
        verbose_name=_('List'),
        max_length=100,
    )
    invert_match = models.BooleanField(
        verbose_name=_('Invert match'),
        default=False,
        help_text=_(
            'Match routes that carry NONE of the listed members (Junos invert-match / '
            'Nokia "expression NOT (…)"). Has no native form on Cisco community-lists.'
        ),
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='community_lists',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Community List')
        verbose_name_plural = 'Community Lists'
        unique_together = ['name']
        ordering = ['name']

    def __str__(self):
        return f'{self.name}'

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('plugins:netbox_routing:communitylist', args=[self.pk])


class Community(PrimaryModel):
    name = models.CharField(
        verbose_name=_('Name'),
        max_length=100,
        blank=True,
    )
    community = models.CharField(
        verbose_name=_('Community'),
        max_length=255,
        # The single universal community field: the member string is stored verbatim, exactly
        # as the device reports it, and its kind (standard/extended/large) is derived by parsing
        # (see community_kind / the `kind` property) — there is no kind column. This holds every
        # form a device emits: numeric standard (1111:100), well-known keywords (no-export),
        # typed extended (target:1111:100, color:0:128), RFC 8092 large (large:GA:L1:L2 or a bare
        # three-part a:b:c), and match-only regex/wildcards (1111:*, 1111:.*, 1111:1113.). Nokia/
        # Junos allow regex inline and Cisco's expanded community-lists are pure regex, so we
        # permit regex metacharacters and letters (keywords) and drop the part cap. A Community
        # holding a regex is match-only — never used in a `set community` (the writer only mints
        # regex members for community-LIST entries).
        validators=[RegexValidator(r'^[\w.:*^$()\[\]|+?\\-]+$')],
    )

    status = models.CharField(
        max_length=50,
        choices=CommunityStatusChoices,
        default=CommunityStatusChoices.STATUS_ACTIVE,
    )
    role = models.ForeignKey(
        verbose_name=_('Role'),
        to='ipam.Role',
        on_delete=models.SET_NULL,
        related_name='communities',
        null=True,
        blank=True,
    )
    tenant = models.ForeignKey(
        verbose_name=_('Tenant'),
        to='tenancy.Tenant',
        on_delete=models.PROTECT,
        related_name='communities',
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = _('Community')
        verbose_name_plural = 'Communities'
        ordering = ['community']
        constraints = [
            models.UniqueConstraint(
                fields=('community',),
                name='%(app_label)s_%(class)s_community',
            ),
        ]

    def __str__(self):
        if self.name:
            return f'{self.name} ({self.community})'
        return f'{self.community}'

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('plugins:netbox_routing:community', args=[self.pk])

    def get_status_color(self):
        return CommunityStatusChoices.colors.get(self.status)

    @property
    def kind(self):
        """Derived kind (standard/extended/large), parsed from the community text."""
        return community_kind(self.community)

    def get_kind_color(self):
        return CommunityKindChoices.colors.get(self.kind)

    def get_kind_display(self):
        return dict(CommunityKindChoices).get(self.kind, self.kind)

    @property
    def match_keyword(self):
        """Device route-map MATCH keyword for this community's kind."""
        return community_match_keyword(self.community)


class CommunityListEntry(PrimaryModel):

    community_list = models.ForeignKey(
        to=CommunityList, on_delete=models.CASCADE, related_name='communitylistentries'
    )
    action = models.CharField(max_length=30, choices=ActionChoices)
    community = models.ForeignKey(
        to=Community,
        related_name='communitylistentries',
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ('community_list', 'community')

    def __str__(self):
        return f'{self.community_list}: {self.action} {self.community}'

    def get_action_color(self):
        return ActionChoices.colors.get(self.action)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse('plugins:netbox_routing:communitylistentry', args=[self.pk])
