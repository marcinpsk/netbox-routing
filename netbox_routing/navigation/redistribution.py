# SPDX-License-Identifier: Apache-2.0

from netbox.plugins import PluginMenuButton, PluginMenuItem

__all__ = ('REDISTRIBUTION_MENU',)

COL_ADD = 'mdi mdi-plus'


redistribution = PluginMenuItem(
    link='plugins:netbox_routing:redistribution_list',
    link_text='Redistribution',
    permissions=['netbox_routing.view_redistribution'],
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_routing:redistribution_add',
            title='Add',
            icon_class=COL_ADD,
            permissions=['netbox_routing.add_redistribution'],
        ),
    ),
)

REDISTRIBUTION_MENU = (redistribution,)
