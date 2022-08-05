from unittest.util import _MAX_LENGTH
import django_tables2 as tables
from django_tables2.utils import Accessor

from dcim.models import Product
from netbox.tables import NetBoxTable
from tenancy.tables import TenancyColumnsMixin
from .template_code import *

__all__ = (
    'ProductTable',
)


def get_cabletermination_row_class(record):
    if record.mark_connected:
        return 'success'
    elif record.cable:
        return record.cable.get_status_color()
    return ''


def get_interface_row_class(record):
    if not record.enabled:
        return 'danger'
    elif record.is_virtual:
        return 'primary'
    return get_cabletermination_row_class(record)


def get_interface_state_attribute(record):
    """
    Get interface enabled state as string to attach to <tr/> DOM element.
    """
    if record.enabled:
        return "enabled"
    else:
        return "disabled"


#
# Products
#

class ProductTable(NetBoxTable):
    name = tables.TemplateColumn(
        order_by=('_name',),
        template_code=PRODUCT_LINK
    )

    class Meta(NetBoxTable.Meta):
        model = Product
        fields = (
            'pk', 'id', 'name', 'comments'
        )
        default_columns = (
            'pk', 'name', 'comments'
        )
