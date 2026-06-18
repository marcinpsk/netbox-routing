from django.utils.translation import gettext_lazy as _

from netbox.ui import attrs, panels

__all__ = (
    'CommunityListPanel',
    'CommunityPanel',
    'CommunityListEntryPanel',
)


class CommunityListPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    invert_match = attrs.BooleanAttr('invert_match', label=_('Invert match'))
    description = attrs.TextAttr('description', label=_('Description'))


class CommunityPanel(panels.ObjectAttributesPanel):
    name = attrs.TextAttr('name', label=_('Name'))
    community = attrs.TextAttr('community', label=_('Community'))
    # Derived from the community text (no stored column); see Community.kind.
    kind = attrs.ChoiceAttr('kind', label=_('Kind'))
    status = attrs.ChoiceAttr('status', label=_('Status'))
    role = attrs.ChoiceAttr('role', label=_('Role'))
    description = attrs.TextAttr('description', label=_('Description'))


class CommunityListEntryPanel(panels.ObjectAttributesPanel):
    community_list = attrs.RelatedObjectAttr('community_list', linkify=True)
    action = attrs.ChoiceAttr('action', label=_('Action'))
    community = attrs.RelatedObjectAttr('community', linkify=True)
    description = attrs.TextAttr('description', label=_('Description'))
