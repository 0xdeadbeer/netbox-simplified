import graphene

from netbox.graphql.fields import ObjectField, ObjectListField
from .types import *


class VirtualizationQuery(graphene.ObjectType):
    cluster_type = ObjectField(ClusterTypeType)
    cluster_type_list = ObjectListField(ClusterTypeType)

    virtual_machine = ObjectField(VirtualMachineType)
    virtual_machine_list = ObjectListField(VirtualMachineType)
