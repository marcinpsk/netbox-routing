from utilities.choices import ChoiceSet


class ActionChoices(ChoiceSet):
    PERMIT = 'permit'
    DENY = 'deny'

    CHOICES = [(PERMIT, 'Permit', 'blue'), (DENY, 'Deny', 'red')]


class CommunitySetActionChoices(ChoiceSet):
    """Operation for a by-reference set-community action on a route-map entry.

    Normalises the vendor verbs: ADD = additive (Junos/Nokia ``add``, IOS-XR ``additive``);
    SET = replace the whole set (Junos ``set``, Nokia ``replace``); DELETE = remove the
    referenced members (Junos ``delete``, Nokia ``remove``).
    """

    ADD = 'add'
    SET = 'set'
    DELETE = 'delete'

    CHOICES = [
        (ADD, 'Add', 'green'),
        (SET, 'Set', 'blue'),
        (DELETE, 'Delete', 'red'),
    ]


class RoutePolicyAFIChoices(ChoiceSet):
    """Address families a route-map entry can match.

    Canonical set across vendors — readers normalise the vendor spellings (Junos
    ``inet``/``inet6`` → ipv4/ipv6, Nokia ``vpn-ipv4`` etc.); anything outside this set is
    preserved under the entry's ``vendor_ext`` rather than dropped.
    """

    IPV4 = 'ipv4'
    IPV6 = 'ipv6'
    VPN_IPV4 = 'vpn-ipv4'
    VPN_IPV6 = 'vpn-ipv6'
    L2VPN = 'l2vpn'

    CHOICES = [
        (IPV4, 'IPv4', 'blue'),
        (IPV6, 'IPv6', 'purple'),
        (VPN_IPV4, 'VPN-IPv4', 'cyan'),
        (VPN_IPV6, 'VPN-IPv6', 'indigo'),
        (L2VPN, 'L2VPN', 'orange'),
    ]


class CommunityStatusChoices(ChoiceSet):
    key = "Community.status"

    STATUS_ACTIVE = 'active'
    STATUS_RESERVED = 'reserved'
    STATUS_DEPRECATED = 'deprecated'

    CHOICES = [
        (STATUS_ACTIVE, 'Active', 'blue'),
        (STATUS_RESERVED, 'Reserved', 'cyan'),
        (STATUS_DEPRECATED, 'Deprecated', 'red'),
    ]


class CommunityKindChoices(ChoiceSet):
    """Derived kind of a Community member, parsed from its text (no stored column)."""

    key = "Community.kind"

    KIND_STANDARD = 'standard'
    KIND_EXTENDED = 'extended'
    KIND_LARGE = 'large'

    CHOICES = [
        (KIND_STANDARD, 'Standard', 'blue'),
        (KIND_EXTENDED, 'Extended', 'purple'),
        (KIND_LARGE, 'Large', 'orange'),
    ]
