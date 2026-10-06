# SPDX-License-Identifier: Apache-2.0

from django.contrib.contenttypes.models import ContentType

from utilities.testing import APIViewTestCases, create_test_device

from netbox_routing.models import ISISInstance, OSPFInstance, Redistribution

__all__ = ('RedistributionAPITestCase',)


class RedistributionAPITestCase(
    APIViewTestCases.GetObjectViewTestCase,
    APIViewTestCases.ListObjectsViewTestCase,
    APIViewTestCases.CreateObjectViewTestCase,
    APIViewTestCases.UpdateObjectViewTestCase,
    APIViewTestCases.DeleteObjectViewTestCase,
):
    """API coverage for Redistribution.

    Composed from the individual API mixins (not the full ``APIViewTestCase``)
    because Redistribution has no GraphQL type — mirroring the fork ``BGPSetting``
    idiom, which is likewise not exposed to GraphQL.
    """

    model = Redistribution
    view_namespace = "plugins-api:netbox_routing"
    brief_fields = [
        'destination',
        'display',
        'id',
        'source_protocol',
        'source_ref',
        'url',
    ]
    bulk_update_data = {'metric': 50}

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Test Device')
        ospf = OSPFInstance.objects.create(
            name='OSPF 1', device=device, router_id='1.1.1.1', process_id='1'
        )
        isis = ISISInstance.objects.create(
            device=device,
            process_tag='CORE',
            net='49.0001.0000.0000.0001.00',
            is_type='level-1-2',
        )
        ospf_ct = ContentType.objects.get_for_model(OSPFInstance)
        isis_ct = ContentType.objects.get_for_model(ISISInstance)

        redistributions = (
            Redistribution(
                destination_type=ospf_ct,
                destination_id=ospf.pk,
                source_protocol='connected',
            ),
            Redistribution(
                destination_type=ospf_ct,
                destination_id=ospf.pk,
                source_protocol='static',
            ),
            Redistribution(
                destination_type=isis_ct,
                destination_id=isis.pk,
                source_protocol='connected',
            ),
        )
        Redistribution.objects.bulk_create(redistributions)

        cls.create_data = [
            {
                'destination_type': 'netbox_routing.ospfinstance',
                'destination_id': ospf.pk,
                'source_protocol': 'bgp',
                'source_ref': '65000',
            },
            {
                'destination_type': 'netbox_routing.isisinstance',
                'destination_id': isis.pk,
                'source_protocol': 'static',
            },
            {
                'destination_type': 'netbox_routing.ospfinstance',
                'destination_id': ospf.pk,
                'source_protocol': 'isis',
                'source_ref': 'CORE',
                'metric': 20,
                'metric_type': '2',
            },
        ]
