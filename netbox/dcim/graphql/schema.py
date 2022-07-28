import graphene

from netbox.graphql.fields import ObjectField, ObjectListField
from .types import *


class DCIMQuery(graphene.ObjectType):

    device = ObjectField(DeviceType)
    device_list = ObjectListField(DeviceType)