# SPDX-License-Identifier: Apache-2.0

from django.contrib.contenttypes.models import ContentType

from utilities.testing import ViewTestCases, create_test_device

from netbox_routing.models import ISISInstance, OSPFInstance, Redistribution

__all__ = ('RedistributionViewTestCase',)


class RedistributionViewTestCase(
    ViewTestCases.GetObjectViewTestCase,
    ViewTestCases.GetObjectChangelogViewTestCase,
    ViewTestCases.CreateObjectViewTestCase,
    ViewTestCases.EditObjectViewTestCase,
    ViewTestCases.DeleteObjectViewTestCase,
    ViewTestCases.ListObjectsViewTestCase,
    ViewTestCases.BulkEditObjectsViewTestCase,
    ViewTestCases.BulkDeleteObjectsViewTestCase,
):
    model = Redistribution

    @classmethod
    def setUpTestData(cls):
        device = create_test_device(name='Device 1')
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

        cls.form_data = {
            'ospf_instance': ospf.pk,
            'source_protocol': 'rip',
            'source_ref': '',
            'metric': 10,
        }

        cls.bulk_edit_data = {
            'metric': 25,
        }

    def _get_base_url(self):
        return 'plugins:netbox_routing:redistribution_{}'
