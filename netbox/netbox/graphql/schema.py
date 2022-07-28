import graphene

from dcim.graphql.schema import DCIMQuery
from extras.graphql.schema import ExtrasQuery
from extras.registry import registry
from tenancy.graphql.schema import TenancyQuery
from users.graphql.schema import UsersQuery
from virtualization.graphql.schema import VirtualizationQuery


class Query(
    DCIMQuery,
    ExtrasQuery,
    TenancyQuery,
    UsersQuery,
    VirtualizationQuery,
    *registry['plugins']['graphql_schemas'],  # Append plugin schemas
    graphene.ObjectType
):
    pass


schema = graphene.Schema(query=Query, auto_camelcase=False)
