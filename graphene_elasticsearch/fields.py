from functools import partial

from elasticsearch_dsl import Search

from promise import Promise

from graphene.types import String
from graphene.relay import ConnectionField, PageInfo
from graphql_relay.connection.arrayconnection import connection_from_list_slice

from graphene_django.settings import graphene_settings


class DocumentConnectionField(ConnectionField):

    def __init__(self, *args, **kwargs):
        self.max_limit = kwargs.pop(
            'max_limit',
            graphene_settings.RELAY_CONNECTION_MAX_LIMIT
        )
        self.enforce_first_or_last = kwargs.pop(
            'enforce_first_or_last',
            graphene_settings.RELAY_CONNECTION_ENFORCE_FIRST_OR_LAST
        )
        super(DocumentConnectionField, self).__init__(*args, **kwargs)

    @property
    def type(self):
        from .types import DocumentObjectType
        _type = super(ConnectionField, self).type
        assert issubclass(_type, DocumentObjectType), "DocumentConnectionField only accepts DocumentObjectType types"
        assert _type._meta.connection, "The type {} doesn't have a connection".format(_type.__name__)
        return _type._meta.connection

    @property
    def node_type(self):
        return self.type._meta.node

    @property
    def doc_type(self):
        return self.node_type._meta.doc_type

    def get_search(self):
        return self.doc_type.search()

    @classmethod
    def merge_searches(cls, default_search, search):
        return search & default_search

    @classmethod
    def resolve_connection(cls, connection, default_search, args, results):
        if results is None:
            results = default_search
        if isinstance(results, Search):
            if results is not default_search:
                results = cls.merge_querysets(default_search, results)
            query = args.get('query')
            if query:
                default_field = args.get('default_field')
                results = results.query('query_string', default_field=default_field, query=query)
            results = results.execute()
        _len = results.hits.total
        connection = connection_from_list_slice(
            results.hits,
            args,
            slice_start=0,
            list_length=_len,
            list_slice_length=_len,
            connection_type=connection,
            edge_type=connection.Edge,
            pageinfo_type=PageInfo,
        )
        connection.iterable = results.hits
        connection.length = _len
        return connection

    @classmethod
    def connection_resolver(cls, resolver, connection, default_search, max_limit,
                            enforce_first_or_last, root, info, **args):
        first = args.get('first')
        last = args.get('last')

        if enforce_first_or_last:
            assert first or last, (
                'You must provide a `first` or `last` value to properly paginate the `{}` connection.'
            ).format(info.field_name)

        if max_limit:
            if first:
                assert first <= max_limit, (
                    'Requesting {} records on the `{}` connection exceeds the `first` limit of {} records.'
                ).format(first, info.field_name, max_limit)
                args['first'] = min(first, max_limit)

            if last:
                assert last <= max_limit, (
                    'Requesting {} records on the `{}` connection exceeds the `last` limit of {} records.'
                ).format(first, info.field_name, max_limit)
                args['last'] = min(last, max_limit)

        results = resolver(root, info, **args)
        on_resolve = partial(cls.resolve_connection, connection, default_search, args)

        if Promise.is_thenable(results):
            return Promise.resolve(results).then(on_resolve)

        return on_resolve(results)

    def get_resolver(self, parent_resolver):
        return partial(
            self.connection_resolver,
            parent_resolver,
            self.type,
            self.get_search(),
            self.max_limit,
            self.enforce_first_or_last
        )
