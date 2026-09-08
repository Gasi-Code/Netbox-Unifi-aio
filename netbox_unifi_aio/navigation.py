from netbox.plugins import PluginMenu, PluginMenuItem, PluginMenuButton
from utilities.choices import ButtonColorChoices

console_item = PluginMenuItem(
    link='plugins:netbox_unifi_aio:uckconsole_list',
    link_text='UCK Consoles',
    buttons=(
        PluginMenuButton(
            link='plugins:netbox_unifi_aio:uckconsole_add',
            title='Console hinzufuegen',
            icon_class='mdi mdi-plus-thick',
            color=ButtonColorChoices.GREEN,
        ),
    ),
)

device_item = PluginMenuItem(
    link='plugins:netbox_unifi_aio:unifidevice_list',
    link_text='UniFi Devices',
)

floorplan_item = PluginMenuItem(
    link='plugins:netbox_unifi_aio:unififloorplanmap_list',
    link_text='Floorplan Maps',
)

synclog_item = PluginMenuItem(
    link='plugins:netbox_unifi_aio:synclog_list',
    link_text='Sync-Logs',
)

menu = PluginMenu(
    label='UniFi AIO',
    groups=(
        ('Verwaltung', (console_item,)),
        ('Network', (device_item,)),
        ('Design', (floorplan_item,)),
        ('Protokoll', (synclog_item,)),
    ),
    icon_class='mdi mdi-router-wireless',
)
