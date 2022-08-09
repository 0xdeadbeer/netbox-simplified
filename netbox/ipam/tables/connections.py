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
    class Meta(NetBoxTable.Meta):
        model = Connection
        fields = (
            'pk', 'id', 'name', 'protocol', 'port', 'comments'
        )
        default_columns = ('pk', 'id', 'name', 'protocol', 'port', 'comments')