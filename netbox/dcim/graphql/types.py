import graphene

from dcim import filtersets, models
from extras.graphql.mixins import (
    ChangelogMixin, ConfigContextMixin, CustomFieldsMixin, ImageAttachmentsMixin, TagsMixin,
)
from netbox.graphql.scalars import BigInt
from netbox.graphql.types import BaseObjectType, OrganizationalObjectType, NetBoxObjectType

__all__ = (
    'ComponentObjectType',
    'ComponentTemplateObjectType',
    'DeviceType'
)


#
# Base types
#

class ComponentObjectType(
    ChangelogMixin,
    CustomFieldsMixin,
    TagsMixin,
    BaseObjectType
):
    """
    Base type for device/VM components
    """
    class Meta:
        abstract = True


class ComponentTemplateObjectType(
    ChangelogMixin,
    BaseObjectType
):
    """
    Base type for device/VM components
    """
    class Meta:
        abstract = True


#
# Model types
#

class DeviceType(ConfigContextMixin, ImageAttachmentsMixin, NetBoxObjectType):

    class Meta:
        model = models.Device
        fields = '__all__'
        filterset_class = filtersets.DeviceFilterSet

    def resolve_face(self, info):
        return self.face or None

    def resolve_airflow(self, info):
        return self.airflow or None
