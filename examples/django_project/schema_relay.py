from graphene import relay
import graphene
from graphene_elasticsearch import DocumentObjectType, DocumentConnectionField

from . import documents


class DocketEntryDocument(DocumentObjectType, interfaces=[relay.Node]):
    case_number = graphene.String()
    case_name = graphene.String()
    title = graphene.String()
    time_filed = graphene.types.datetime.DateTime()
    court_name = graphene.String()
    court_abbr = graphene.String()

    class Meta:
        doc_type = documents.DocketEntryDocument

    def resolve_court_name(self, info):
        return self.court.name

    def resolve_court_abbr(self, info):
        return self.court.abbr


class Query(graphene.ObjectType):
    docket_entry_document = relay.Node.Field(DocketEntryDocument)
    all_docket_entry_documents = DocumentConnectionField(
        DocketEntryDocument,
        default_field=graphene.String(),
        query=graphene.String(),
    )
