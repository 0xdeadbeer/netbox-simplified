import django_tables2 as tables

from ipam.models import *
from netbox.tables import NetBoxTable, columns
from .template_code import *

__all__ = (
    'ConnectionTable',
)

class ConnectionTable(NetBoxTable): 
    name = tables.Column (
        linkify=True 
    )
    protocol = tables.TemplateColumn ( 
        template_code=PROTOCOL_TABLE_TEMPLATE
    )
    port = tables.TemplateColumn (
        template_code=PORT_TABLE_TEMPLATE
    )
    device_from = tables.TemplateColumn (
        verbose_name='Device From',
        template_code=DEVICE_FROM_DISPLAY
    )
    device_to = tables.TemplateColumn (
        verbose_name='Device to',
        template_code=DEVICE_TO_DISPLAY
    )

    class Meta(NetBoxTable.Meta):
        model = Connection
        fields = (
            'pk', 'id', 'name', 'protocol', 'port', 'comments', 'products', 'programs'
        )
        default_columns = ('pk', 'id', 'name', 'protocol', 'port', 'comments', 'products', 'programs')