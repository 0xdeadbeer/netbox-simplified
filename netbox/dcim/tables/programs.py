import django_tables2 as tables

from dcim.models import Program
from netbox.tables import NetBoxTable
from .template_code import *

__all__ = (
    'ProgramTable',
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
# Programs
#

class ProgramTable(NetBoxTable):
    name = tables.TemplateColumn(
        order_by=('_name',),
        template_code=PROGRAMS_LINK
    )
    devices = tables.TemplateColumn (
        verbose_name='Devices',
        template_code=PROGRAMS_DEVICE_DISPLAY
    )

    class Meta(NetBoxTable.Meta):
        model = Program
        fields = (
            'pk', 'id', 'name', 'comments', 'devices' 
        )
        default_columns = (
            'pk', 'name', 'comments', 'devices'
        )
