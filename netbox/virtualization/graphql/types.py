from dcim.graphql.types import ComponentObjectType
from extras.graphql.mixins import ConfigContextMixin
from netbox.graphql.types import OrganizationalObjectType, NetBoxObjectType
from virtualization import filtersets, models

__all__ = (
    'ClusterTypeType',
    'VirtualMachineType',
)




class ClusterTypeType(OrganizationalObjectType):

    class Meta:
        model = models.ClusterType
        fields = '__all__'
        filterset_class = filtersets.ClusterTypeFilterSet


class VirtualMachineType(ConfigContextMixin, NetBoxObjectType):

    class Meta:
        model = models.VirtualMachine
        fields = '__all__'
        filterset_class = filtersets.VirtualMachineFilterSet
