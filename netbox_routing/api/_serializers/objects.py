from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from netbox.api.fields import ContentTypeField
from netbox.api.gfk_fields import GFKSerializerField
from netbox.api.serializers import NetBoxModelSerializer
from netbox_routing.constants.objects import PREFIX_ASSIGNMENT_MODELS
from netbox_routing.models.objects import *
from netbox_routing.api._serializers.community import *

__all__ = (
    'ASPathSerializer',
    'ASPathEntrySerializer',
    'CustomPrefixSerializer',
    'PrefixListSerializer',
    'PrefixListEntrySerializer',
    'RouteMapSerializer',
    'RouteMapEntrySerializer',
    'RouteMapEntrySetCommunitySerializer',
)


class ASPathSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing-api:aspath-detail'
    )

    class Meta:
        model = ASPath
        fields = (
            'url',
            'id',
            'display',
            'name',
            'description',
            'comments',
        )
        brief_fields = ('url', 'id', 'display', 'name')


class ASPathEntrySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing-api:aspathentry-detail'
    )
    aspath = ASPathSerializer(nested=True)

    class Meta:
        model = ASPathEntry
        fields = (
            'url',
            'id',
            'display',
            'aspath',
            'sequence',
            'action',
            'pattern',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'aspath',
            'sequence',
            'action',
            'pattern',
        )


class PrefixListSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing-api:prefixlist-detail'
    )

    class Meta:
        model = PrefixList
        fields = (
            'url',
            'id',
            'display',
            'name',
            'description',
            'comments',
            'custom_fields',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'name',
        )


class PrefixListEntrySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing-api:prefixlistentry-detail'
    )
    prefix_list = PrefixListSerializer(nested=True)
    assigned_prefix_type = ContentTypeField(
        queryset=ContentType.objects.filter(PREFIX_ASSIGNMENT_MODELS),
        allow_null=True,
        required=False,
        default=None,
    )
    assigned_prefix_id = serializers.IntegerField(
        allow_null=True, required=False, default=None
    )
    assigned_prefix = GFKSerializerField(read_only=True)

    class Meta:
        model = PrefixListEntry
        fields = (
            'url',
            'id',
            'display',
            'prefix_list',
            'sequence',
            'action',
            'assigned_prefix_type',
            'assigned_prefix_id',
            'assigned_prefix',
            'le',
            'ge',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'prefix_list',
            'sequence',
            'action',
            'assigned_prefix_type',
            'assigned_prefix_id',
            'le',
            'ge',
        )


class CustomPrefixSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing-api:customprefix-detail'
    )

    class Meta:
        model = CustomPrefix
        fields = (
            'url',
            'id',
            'display',
            'prefix',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'prefix',
        )


class RouteMapSerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing-api:prefixlist-detail'
    )

    class Meta:
        model = RouteMap
        fields = (
            'url',
            'id',
            'display',
            'name',
            'default_action',
            'description',
            'comments',
        )
        brief_fields = ('url', 'id', 'display', 'name')


class RouteMapEntrySetCommunitySerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing-api:routemapentrysetcommunity-detail'
    )
    route_map_entry = serializers.PrimaryKeyRelatedField(
        queryset=RouteMapEntry.objects.all()
    )
    community_list = CommunityListSerializer(
        nested=True, required=False, allow_null=True
    )
    communities = CommunitySerializer(nested=True, many=True, required=False)

    class Meta:
        model = RouteMapEntrySetCommunity
        fields = (
            'id',
            'url',
            'route_map_entry',
            'operation',
            'community_list',
            'communities',
        )

    def validate(self, data):
        data = super().validate(data)
        # Every operation (add/set/delete) acts on communities, so a set-community
        # action must reference a community list and/or carry inline communities.
        # Without either it is a no-op that renders as a misleading empty "inline"
        # action. (This lives in the serializer rather than model.clean() because
        # `communities` is an M2M — unpopulated until after save — so a model-level
        # clean cannot see it.)
        community_list = data.get('community_list')
        communities = data.get('communities')
        if self.instance is not None:
            # Partial update: fall back to the stored value for any field not supplied.
            if 'community_list' not in data:
                community_list = self.instance.community_list
            if 'communities' not in data:
                communities = list(self.instance.communities.all())
        if not community_list and not communities:
            raise serializers.ValidationError(
                'A set-community action must reference a community list '
                'and/or inline communities.'
            )
        return data

    def create(self, validated_data):
        communities = validated_data.pop('communities', None)
        instance = super().create(validated_data)
        return self._set_communities(instance, communities)

    def update(self, instance, validated_data):
        communities = validated_data.pop('communities', None)
        instance = super().update(instance, validated_data)
        return self._set_communities(instance, communities)

    @staticmethod
    def _set_communities(instance, communities):
        if communities is not None:
            instance.communities.set(communities)
        return instance


class RouteMapEntrySerializer(NetBoxModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='plugins-api:netbox_routing-api:prefixlistentry-detail'
    )
    route_map = RouteMapSerializer(nested=True)
    match_prefix_list = PrefixListSerializer(nested=True, many=True, required=False)
    match_community_list = CommunityListSerializer(
        nested=True, many=True, required=False
    )
    match_community = CommunitySerializer(nested=True, many=True, required=False)
    match_aspath = ASPathSerializer(nested=True, many=True, required=False)
    call_policy = RouteMapSerializer(nested=True, required=False, allow_null=True)
    apply_policy = RouteMapSerializer(nested=True, required=False, allow_null=True)
    set_communities = RouteMapEntrySetCommunitySerializer(many=True, read_only=True)

    class Meta:
        model = RouteMapEntry
        fields = (
            'url',
            'id',
            'display',
            'route_map',
            'sequence',
            'action',
            'match_prefix_list',
            'match_community_list',
            'match_community',
            'match_aspath',
            'match_afi',
            'match_condition',
            'call_policy',
            'apply_policy',
            'match',
            'set',
            'set_communities',
            'vendor_ext',
            'description',
            'comments',
        )
        brief_fields = (
            'url',
            'id',
            'display',
            'route_map',
            'sequence',
            'action',
        )
