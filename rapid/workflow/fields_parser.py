from typing import Dict, List, Type, Union

from sqlalchemy.orm import Load, joinedload


class RelationshipParser:
    def __init__(self, relationship_str: str):
        self._rel_str: Union[str, None] = None
        self._rel_fields: Union[List[str], None] = []

        self._split(relationship_str)

    def _split(self, relationship_str: str) -> None:
        if relationship_str:
            rel_split = relationship_str.split('=')
            if len(rel_split) == 1:
                self._rel_str = None
                self._rel_fields = rel_split[0].split(',')
            else:
                self._rel_str = rel_split[0]
                self._rel_fields = rel_split[1].split(',')

    @property
    def relationship(self) -> Union[str, None]:
        return self._rel_str

    @property
    def fields(self) -> List[str]:
        return self._rel_fields


class FieldsParser:
    """
    The FieldsParser will take embedded and nested relationships and make sure left joins are added
    making sure things are faster.  The structure is:

    field1,field2,field;field1=1_field;field2=2_field;1_field=1_1_field

    fields are separated by commas.
    Relationships are distinguished by an '=' sign.
    Each level is separated by the ';' symbol

    If any of those fields are relationships, then they will be added to the join. This speeds the API
    up exceptionally.
    """
    def __init__(self, root_class: Type[any], fields: str):
        self._root_class = root_class
        self._fields:str = fields
        self._fields_mapping:Dict[str, List[str]] = {root_class.__tablename__: []}
        self._mappings:Dict[str, Type[any]] = {}
        self._field_loads:Dict[Type[any], any] = {}
        self._attribute_mapping = {}

        self._parse_fields()

    def field_joins(self) -> List[Load]:
        return list(self._field_loads.values())

    def fields_mapping(self) -> Dict[str, List[str]]:
        return self._fields_mapping

    def _add_field_mapping(self, clazz, field: str):
        try:
            attr = getattr(clazz, field)
            self._mappings[field] = attr.mapper.class_
        except:
            ...

    def _parse_root_fields(self, parser: RelationshipParser):
        for field in parser.fields:
            if field:
                self._add_field_mapping(self._root_class, field)
                field_mapping = self._mappings[field]
                if field_mapping not in self._field_loads:
                    self._field_loads[field_mapping] = joinedload(getattr(self._root_class, field))
                self._fields_mapping[self._root_class.__tablename__].append(field)

    def _parse_relationship_fields(self, parser: RelationshipParser):
        relationship_mapping = self._mappings[parser.relationship]

        for field in parser.fields:
            if field:
                self._add_field_mapping(relationship_mapping, field)
                if parser.relationship in self._mappings:
                    _joined = self._field_loads[relationship_mapping].joinedload(getattr(relationship_mapping, field))
                    self._field_loads[self._mappings[field]] = _joined
                if parser.relationship not in self._fields_mapping:
                    self._fields_mapping[parser.relationship] = []
                self._fields_mapping[parser.relationship].append(field)

    def _parse_fields(self):
        if self._fields:
            try:
                for relationship_str in self._fields.split(';'):
                    parser = RelationshipParser(relationship_str)
                    if parser.relationship or parser.fields:
                        if parser.relationship is None:
                            self._parse_root_fields(parser)
                        else:
                            self._parse_relationship_fields(parser)
            except AttributeError:
                pass
