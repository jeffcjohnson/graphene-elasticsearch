from graphene.relay import Connection, Node
from graphene.types.objecttype import ObjectType, ObjectTypeOptions
import django_elasticsearch_dsl


class DocumentObjectTypeOptions(ObjectTypeOptions):
    doc_type: django_elasticsearch_dsl.DocType = None
    connection = None  # type: Type[Connection]


class DocumentObjectType(ObjectType):
    @classmethod
    def __init_subclass_with_meta__(cls, doc_type=None, connection=None,
                                    use_connection=None, interfaces=(), **options):

        if use_connection is None and interfaces:
            use_connection = any((issubclass(interface, Node) for interface in interfaces))

        if use_connection and not connection:
            # We create the connection automatically
            connection = Connection.create_type('{}Connection'.format(cls.__name__), node=cls)

        if connection is not None:
            assert issubclass(connection, Connection), (
                "The connection must be a Connection. Received {}"
            ).format(connection.__name__)

        _meta = DocumentObjectTypeOptions(cls)
        _meta.doc_type = doc_type
        _meta.connection = connection

        super(DocumentObjectType, cls).__init_subclass_with_meta__(_meta=_meta, interfaces=interfaces, **options)

    def resolve_id(self, info):
        return self._id

    @classmethod
    def get_node(cls, info, id):
        return cls._meta.doc_type.get(id)
