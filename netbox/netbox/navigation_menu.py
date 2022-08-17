from dataclasses import dataclass
from typing import Sequence, Optional

from extras.registry import registry
from utilities.choices import ButtonColorChoices


#
# Nav menu data classes
#

@dataclass
class MenuItemButton:

    link: str
    title: str
    icon_class: str
    permissions: Optional[Sequence[str]] = ()
    color: Optional[str] = None


@dataclass
class MenuItem:

    link: str
    link_text: str
    permissions: Optional[Sequence[str]] = ()
    buttons: Optional[Sequence[MenuItemButton]] = ()


@dataclass
class MenuGroup:

    label: str
    items: Sequence[MenuItem]


@dataclass
class Menu:

    label: str
    icon_class: str
    groups: Sequence[MenuGroup]


#
# Utility functions
#

def get_model_item(app_label, model_name, label, actions=('add', 'import')):
    return MenuItem(
        link=f'{app_label}:{model_name}_list',
        link_text=label,
        permissions=[f'{app_label}.view_{model_name}'],
        buttons=get_model_buttons(app_label, model_name, actions)
    )


def get_model_buttons(app_label, model_name, actions=('add', 'import')):
    buttons = []

    if 'add' in actions:
        buttons.append(
            MenuItemButton(
                link=f'{app_label}:{model_name}_add',
                title='Add',
                icon_class='mdi mdi-plus-thick',
                permissions=[f'{app_label}.add_{model_name}'],
                color=ButtonColorChoices.GREEN
            )
        )
    if 'import' in actions:
        buttons.append(
            MenuItemButton(
                link=f'{app_label}:{model_name}_import',
                title='Import',
                icon_class='mdi mdi-upload',
                permissions=[f'{app_label}.add_{model_name}'],
                color=ButtonColorChoices.CYAN
            )
        )

    return buttons


#
# Nav menus
#

DEVICES_MENU = Menu(
    label='Servers',
    icon_class='mdi mdi-server',
    groups=(
        MenuGroup(
            label='Servers',
            items=(
                get_model_item('dcim', 'device', 'Servers', ('add')),
                get_model_item('dcim', 'devicerole', 'Server Roles', ('add')),
                get_model_item('dcim', 'product', 'Products', ('add')),
                get_model_item('dcim', 'program', 'Programs', ('add')),
            ),
        ),
    ),
)

IPAM_MENU = Menu(
    label='Connections',
    icon_class='mdi mdi-counter',
    groups=(
        MenuGroup(
            label='Connections',
            items=(
                get_model_item('ipam', 'service', 'Ports', ('add')),
                get_model_item('ipam', 'servicetemplate', 'Port templates', ('add')),
                get_model_item('ipam', 'connection', 'Server Connections', ('add')),
            ),
        ),
    ),
)

OTHER_MENU = Menu(
    label='Other',
    icon_class='mdi mdi-notification-clear-all',
    groups=(
        MenuGroup(
            label='Logging',
            items=(
                get_model_item('extras', 'journalentry', 'Journal Entries', actions=[]),
                get_model_item('extras', 'objectchange', 'Change Log', actions=[]),
            ),
        ),
        MenuGroup(
            label='Customization',
            items=(
                get_model_item('extras', 'customfield', 'Custom Fields'),
                get_model_item('extras', 'customlink', 'Custom Links'),
                get_model_item('extras', 'exporttemplate', 'Export Templates'),
            ),
        ),
        MenuGroup(
            label='Integrations',
            items=(
                get_model_item('extras', 'webhook', 'Webhooks'),
                MenuItem(
                    link='extras:report_list',
                    link_text='Reports',
                    permissions=['extras.view_report']
                ),
                MenuItem(
                    link='extras:script_list',
                    link_text='Scripts',
                    permissions=['extras.view_script']
                ),
            ),
        ),
        MenuGroup(
            label='Other',
            items=(
                get_model_item('extras', 'tag', 'Tags'),
                get_model_item('extras', 'configcontext', 'Config Contexts', actions=['add']),
            ),
        ),
    ),
)


MENUS = [
    DEVICES_MENU,
    IPAM_MENU,
    OTHER_MENU,
]

#
# Add plugin menus
#

if registry['plugins']['menu_items']:
    plugin_menu_groups = []

    for plugin_name, items in registry['plugins']['menu_items'].items():
        plugin_menu_groups.append(
            MenuGroup(
                label=plugin_name,
                items=items
            )
        )

    PLUGIN_MENU = Menu(
        label="Plugins",
        icon_class="mdi mdi-puzzle",
        groups=plugin_menu_groups
    )

    MENUS.append(PLUGIN_MENU)
