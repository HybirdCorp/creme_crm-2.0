# -*- coding: utf-8 -*-

################################################################################
#    Creme is a free/open-source Customer Relationship Management software
#    Copyright (C) 2009-2017  Hybird
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

from collections import defaultdict
import logging

from django.contrib.contenttypes.models import ContentType
from django.db.models import Q, CharField, ForeignKey, ManyToManyField, BooleanField, PROTECT, CASCADE
from django.db.transaction import atomic
from django.dispatch import receiver
from django.http import Http404
from django.utils.translation import ugettext_lazy as _, ugettext

from ..signals import pre_merge_related

from .base import CremeModel, CremeAbstractEntity
from .creme_property import CremePropertyType
from .entity import CremeEntity


logger = logging.getLogger(__name__)


class RelationType(CremeModel):
    """
    If *_ctypes = null --> all ContentTypes are valid.
    If *_properties = null --> all CremeProperties are valid.
    """
    id = CharField(primary_key=True, max_length=100)  # NB: convention: 'app_name-foobar'
                                                      # BEWARE: 'id' MUST only contain alphanumeric '-' and '_'

    subject_ctypes     = ManyToManyField(ContentType,       blank=True, related_name='relationtype_subjects_set')
    object_ctypes      = ManyToManyField(ContentType,       blank=True, related_name='relationtype_objects_set')
    subject_properties = ManyToManyField(CremePropertyType, blank=True, related_name='relationtype_subjects_set')
    object_properties  = ManyToManyField(CremePropertyType, blank=True, related_name='relationtype_objects_set')

    is_internal = BooleanField(default=False)  # If True, the relations with this type cannot
                                               #  be created/deleted directly by the users.
    is_custom   = BooleanField(default=False)  # If True, the RelationType can ot be deleted (in creme_config).
    is_copiable = BooleanField(default=True)   # If True, the relations with this type can be copied
                                               #  (ie when cloning or converting an entity)

    # Try to display the relationships of this type only once in the detail-views ?
    # ie: does not display them in the general relationships bricks when another bricks manage this type.
    minimal_display = BooleanField(default=False)

    predicate      = CharField(_(u'Predicate'), max_length=100)
    symmetric_type = ForeignKey('self', blank=True, null=True, on_delete=CASCADE)

    creation_label = _(u'Create a type of relationship')
    save_label     = _(u'Save the type')

    class Meta:
        app_label = 'creme_core'
        verbose_name = _(u'Type of relationship')
        verbose_name_plural = _(u'Types of relationship')
        ordering = ('predicate',)

    def __unicode__(self):
        sym_type = self.symmetric_type
        symmetric_pred = ugettext(u'No relationship') if sym_type is None else sym_type.predicate
        return u'%s — %s' % (self.predicate, symmetric_pred)  # NB: — == "\xE2\x80\x94" == &mdash;

    def add_subject_ctypes(self, *models):
        get_ct = ContentType.objects.get_for_model
        cts = [get_ct(model) for model in models]
        self.subject_ctypes.add(*cts)
        self.symmetric_type.object_ctypes.add(*cts)

    # def delete(self):
    def delete(self, using=None):
        sym_type = self.symmetric_type

        super(RelationType, sym_type).delete(using=using)
        super(RelationType, self).delete(using=using)

    @staticmethod
    def get_compatible_ones(ct, include_internals=False):
        types = RelationType.objects.filter(Q(subject_ctypes=ct) | Q(subject_ctypes__isnull=True))
        if not include_internals:
            types = types.filter(Q(is_internal=False))

        return types

    @staticmethod
    @atomic
    def create(subject_desc, object_desc, is_custom=False, generate_pk=False, is_internal=False,
               is_copiable=(True, True), minimal_display=(False, False)):
        """
        @param subject_desc: Tuple (string_pk, predicate_string [, sequence_of_cremeEntityClasses [, sequence_of_propertyTypes]])
        @param object_desc: See subject_desc.
        @param generate_pk: If True, 'string_pk' args are used as prefix to generate pks.
        """
        padding       = ((), ())  # In case sequence_of_cremeEntityClasses or sequence_of_propertyType not given.
        subject_desc += padding
        object_desc  += padding

        if isinstance(is_copiable, bool):
            is_copiable = (is_copiable, is_copiable)

        pk_subject   = subject_desc[0]
        pk_object    = object_desc[0]
        pred_subject = subject_desc[1]
        pred_object  = object_desc[1]

        if not generate_pk:
            update_or_create = RelationType.objects.update_or_create
            defaults = {'is_custom': is_custom, 'is_internal': is_internal}
            sub_relation_type = update_or_create(id=pk_subject,
                                                 defaults=dict(defaults,
                                                               predicate=pred_subject,
                                                               is_copiable=is_copiable[0],
                                                               minimal_display=minimal_display[0],
                                                              )
                                                )[0]
            obj_relation_type = update_or_create(id=pk_object,
                                                 defaults=dict(defaults,
                                                               predicate=pred_object,
                                                               is_copiable=is_copiable[1],
                                                               minimal_display=minimal_display[1],
                                                              )
                                                )[0]
        else:
            from creme.creme_core.utils.id_generator import generate_string_id_and_save

            sub_relation_type = RelationType(predicate=pred_subject, is_custom=is_custom, is_internal=is_internal,
                                             is_copiable=is_copiable[0], minimal_display=minimal_display[0],
                                            )
            obj_relation_type = RelationType(predicate=pred_object,  is_custom=is_custom, is_internal=is_internal,
                                             is_copiable=is_copiable[1], minimal_display=minimal_display[1],
                                            )

            generate_string_id_and_save(RelationType, [sub_relation_type], pk_subject)
            generate_string_id_and_save(RelationType, [obj_relation_type], pk_object)

        sub_relation_type.symmetric_type = obj_relation_type
        obj_relation_type.symmetric_type = sub_relation_type

        # Delete old m2m (TODO: just remove useless ones ???)
        for rt in (sub_relation_type, obj_relation_type):
            rt.subject_ctypes.clear()
            rt.subject_properties.clear()
            rt.object_ctypes.clear()
            rt.object_properties.clear()

        get_ct = ContentType.objects.get_for_model

        for subject_ctype in subject_desc[2]:
            ct = get_ct(subject_ctype)
            sub_relation_type.subject_ctypes.add(ct)
            obj_relation_type.object_ctypes.add(ct)

        for object_ctype in object_desc[2]:
            ct = get_ct(object_ctype)
            sub_relation_type.object_ctypes.add(ct)
            obj_relation_type.subject_ctypes.add(ct)

        for subject_prop in subject_desc[3]:
            sub_relation_type.subject_properties.add(subject_prop)
            obj_relation_type.object_properties.add(subject_prop)

        for object_prop in object_desc[3]:
            sub_relation_type.object_properties.add(object_prop)
            obj_relation_type.subject_properties.add(object_prop)

        sub_relation_type.save()
        obj_relation_type.save()

        return sub_relation_type, obj_relation_type

    def is_compatible(self, ctype_id):
        # TODO: check if self.subject_ctypes.all() is already retrieved (prefetch_related)?
        subject_ctypes = frozenset(self.subject_ctypes.values_list('id', flat=True))

        return not subject_ctypes or ctype_id in subject_ctypes

    def is_not_internal_or_die(self):
        if self.is_internal:
            raise Http404(ugettext(u"You can't add/delete the relationships with this type (internal type)"))


# TODO: remove CremeAbstractEntity inheritance (user/modified not useful any more ??) ??
class Relation(CremeAbstractEntity):
    type               = ForeignKey(RelationType, blank=True, null=True, on_delete=CASCADE)  # TODO: nullable=False
    symmetric_relation = ForeignKey('self', blank=True, null=True, on_delete=CASCADE)
    subject_entity     = ForeignKey(CremeEntity, related_name='relations', on_delete=PROTECT)
    object_entity      = ForeignKey(CremeEntity, related_name='relations_where_is_object', on_delete=PROTECT)

    class Meta:
        app_label = 'creme_core'
        verbose_name = _(u'Relationship')
        verbose_name_plural = _(u'Relationships')

    def __unicode__(self):
        return u'«%s» %s «%s»' % (self.subject_entity, self.type, self.object_entity)

    def _build_symmetric_relation(self, update):
        """Overload me in child classes.
        @param update: Boolean. True->updating object ; False->creating object.
        """
        if update:
            sym_relation = self.symmetric_relation
            assert sym_relation
        else:
            sym_relation = Relation(user=self.user,
                                    type=self.type.symmetric_type,
                                    symmetric_relation=self,
                                    subject_entity=self.object_entity,
                                    object_entity=self.subject_entity,
                                   )

        return sym_relation

    @atomic
    # def save(self, using='default', force_insert=False):
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """See django.db.models.Model.save()

        @param force_update: Not used.
        @param update_fields: Not used.
        """
        update = bool(self.pk)

        super(Relation, self).save(using=using, force_insert=force_insert)

        sym_relation = self._build_symmetric_relation(update)
        super(Relation, sym_relation).save(using=using, force_insert=force_insert)

        if self.symmetric_relation is None:
            self.symmetric_relation = sym_relation
            super(Relation, self).save(using=using, force_insert=False)

    def get_real_entity(self):
        return self._get_real_entity(Relation)

    @staticmethod
    def populate_real_object_entities(relations):
        """Faster than call get_real_entity() on each relation.object_entity.
        @param relations: Iterable of Relation objects.

        Tips: better if object_entity attribute is already populated
        -> (eg: use select_related('object_entity') on the queryset)
        """
        CremeEntity.populate_real_entities([relation.object_entity for relation in relations])

    # TODO: remove 'model' ; rename other args... (move to EntityCellRelation ??)
    @staticmethod
    def filter_in(model, filter_predicate, value_for_filter):
        return Q(relations__type=filter_predicate,
                 relations__object_entity__header_filter_search_field__icontains=value_for_filter,
                 )


class SemiFixedRelationType(CremeModel):
    predicate     = CharField(_(u'Predicate'), max_length=100, unique=True)
    relation_type = ForeignKey(RelationType, on_delete=CASCADE)
    object_entity = ForeignKey(CremeEntity, on_delete=CASCADE)

    creation_label = _(u'Create a semi-fixed type of relationship')
    save_label     = _(u'Save the type')

    class Meta:
        app_label = 'creme_core'
        unique_together = ('relation_type', 'object_entity')
        verbose_name = _(u'Semi-fixed type of relationship')
        verbose_name_plural = _(u'Semi-fixed types of relationship')
        ordering = ('predicate',)

    def __unicode__(self):
        return self.predicate


# @receiver(pre_merge_related)
# def _handle_merge(sender, other_entity, **kwargs):
#     """Delete 'Duplicated' Relations (ie: exist in the removed entity & the
#     remaining entity).
#     """
#     from .history import HistoryLine
#
#     # TRICK: We use the related accessor 'relations_where_is_object' instead
#     # of 'relations' because HistoryLine creates lines for relation with
#     # types '*-subject_*' (symmetric with types '*-object_*')
#     # If we'd use 'sender.relations' we should disable/delete
#     # 'relation.symmetric_relation' that would take an additional query.
#     relations_info = defaultdict(list)
#     for rtype_id, entity_id in sender.relations_where_is_object \
#                                      .values_list('type', 'subject_entity'):
#         relations_info[rtype_id].append(entity_id)
#
#     rel_filter = other_entity.relations_where_is_object.filter
#     for rtype_id, entity_ids in relations_info.iteritems():
#         for relation in rel_filter(type=rtype_id, subject_entity__in=entity_ids):
#             HistoryLine.disable(relation)
#             relation.delete()
@receiver(pre_merge_related)
def _handle_merge(sender, other_entity, **kwargs):
    """The generic creme_core.utils.replace_related_object() cannot correctly
    handle the Relation model :
      - we have to keep the uniqueness of (subject, type, object)
      - replacing the remaining entity as subject/object in the Relations of
        'other_entity' should not create multiple HistoryLines.
        (because with the symmetric relationships feature, its tricky).

    So this handler does the job i the right way:
      - it deletes the 'duplicated' Relations (ie: exist in the removed entity
        & the remaining entity), without creating HistoryLines at all.
      - it updates the relationships which reference the removed entity to
        reference the remaining entity (History is managed by hand).
    """
    from .history import HistoryLine, _HLTRelation

    # Deletion of duplicates ---------------------------------------------------

    # Key#1 => relation-type ID
    # Key#2 => object_entity ID (linked to at least one of the merged entities)
    # Value => set of merged entities IDs (so 1 or 2 IDs between [sender.id, other_entity.id])
    entities_per_rtype_ids = defaultdict(lambda: defaultdict(set))

    for merged_id, rtype_id, object_id in \
            RelationType.objects.filter(relation__subject_entity__in=(sender.id, other_entity.id)) \
                                .values_list('relation__subject_entity_id', 'id', 'relation__object_entity_id'):
        entities_per_rtype_ids[rtype_id][object_id].add(merged_id)

    duplicates_q = Q()
    for rtype_id, entities_dict in entities_per_rtype_ids.iteritems():
        for object_id, subject_ids in entities_dict.iteritems():
            if len(subject_ids) > 1:
                duplicates_q |= Q(type=rtype_id, object_entity=object_id)

    del entities_per_rtype_ids  # free memory

    if duplicates_q:
        for relation in other_entity.relations.filter(duplicates_q) \
                                    .select_related('symmetric_relation'):
            # NB: HistoryLine.disable() work only on the '-subject_' side of the Relation
            if '-subject_' not in relation.type_id:
                relation = relation.symmetric_relation

            HistoryLine.disable(relation)
            relation.delete()

    # Replacement of ForeignKeys -----------------------------------------------

    for relation in other_entity.relations.select_related('symmetric_relation'):
        relation.subject_entity = sender
        relation.symmetric_relation.object_entity = sender
        # NB: <created=False> because the function create lines only at edition
        #     (to ensure the 2 linked Relation instances are created).
        _HLTRelation.create_lines(relation, created=False)

    other_entity.relations.update(subject_entity=sender)
    other_entity.relations_where_is_object.update(object_entity=sender)
