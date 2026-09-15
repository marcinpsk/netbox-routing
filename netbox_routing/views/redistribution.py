# SPDX-License-Identifier: Apache-2.0

from extras.ui.panels import TagsPanel
from netbox.ui import layout, panels
from netbox.views.generic import (
    BulkDeleteView,
    BulkEditView,
    ObjectDeleteView,
    ObjectEditView,
    ObjectListView,
    ObjectView,
)
from utilities.views import register_model_view

from netbox_routing.filtersets.redistribution import RedistributionFilterSet
from netbox_routing.forms.bulk_edit.redistribution import RedistributionBulkEditForm
from netbox_routing.forms.filtersets.redistribution import RedistributionFilterForm
from netbox_routing.forms.model_objects.redistribution import RedistributionForm
from netbox_routing.models.redistribution import Redistribution
from netbox_routing.tables.redistribution import RedistributionTable
from netbox_routing.ui import RedistributionPanel

__all__ = (
    'RedistributionListView',
    'RedistributionView',
    'RedistributionEditView',
    'RedistributionDeleteView',
    'RedistributionBulkEditView',
    'RedistributionBulkDeleteView',
)


@register_model_view(Redistribution, name='list', path='', detail=False)
class RedistributionListView(ObjectListView):
    queryset = Redistribution.objects.all()
    filterset = RedistributionFilterSet
    filterset_form = RedistributionFilterForm
    table = RedistributionTable


@register_model_view(Redistribution)
class RedistributionView(ObjectView):
    queryset = Redistribution.objects.all()
    template_name = 'generic/object.html'
    layout = layout.SimpleLayout(
        left_panels=[
            RedistributionPanel(),
            TagsPanel(),
        ],
        right_panels=[
            panels.CommentsPanel(),
            panels.RelatedObjectsPanel(),
        ],
    )


@register_model_view(Redistribution, name='add', detail=False)
@register_model_view(Redistribution, name='edit')
class RedistributionEditView(ObjectEditView):
    queryset = Redistribution.objects.all()
    form = RedistributionForm


@register_model_view(Redistribution, name='delete')
class RedistributionDeleteView(ObjectDeleteView):
    queryset = Redistribution.objects.all()


@register_model_view(Redistribution, name='bulk_edit', detail=False)
class RedistributionBulkEditView(BulkEditView):
    queryset = Redistribution.objects.all()
    filterset = RedistributionFilterSet
    form = RedistributionBulkEditForm
    table = RedistributionTable


@register_model_view(Redistribution, name='bulk_delete', detail=False)
class RedistributionBulkDeleteView(BulkDeleteView):
    queryset = Redistribution.objects.all()
    filterset = RedistributionFilterSet
    table = RedistributionTable
