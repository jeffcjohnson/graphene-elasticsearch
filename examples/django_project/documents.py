from django_elasticsearch_dsl import DocType, Index, fields
from . import models


entries = Index('docket-entries')

entries.settings(
    number_of_shards=1,
    number_of_replicas=0
)


# @entries.doc_type
class DocketEntryDocument(DocType):
    court = fields.ObjectField(
        properties={
            'description': fields.TextField(),
            'name': fields.KeywordField(),
        }
    )

    case = fields.ObjectField(
        properties={
            'year': fields.KeywordField(),
            'number': fields.KeywordField(),
            'office': fields.KeywordField(),
            'type': fields.KeywordField(),
        }
    )

    class Meta:
        model = models.DocketEntry
        fields = [
            'case_number',
            'case_name',
            'title',
            'time_filed',
        ]
        # related_models = [models.Court]
        ignore_signals = True
        auto_refresh = False

    def get_queryset(self):
        qs = super().get_queryset().select_related('court')
        # FIXME out of +1M entries, only 10 have a blank case_name, for now just exclude them
        qs = qs.exclude(case_name='')  # ES doesn't allow emtpy values on completions
        qs = qs[:1000]  # for testing only index the first X items
        return qs

    # def get_instances_from_related(self, related_instance):
    #     return related_instance.docket_entry_set.all()

