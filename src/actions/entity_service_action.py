from abc import ABC
from typing import ClassVar

from src.actions import Action
from src.services.entity_service import EntityService


class EntityServiceAction(Action, ABC):
    not_editable_fields: ClassVar[frozenset[str]] = frozenset("id",)
    def __init__(self, service: EntityService):
        super().__init__()
        self.service = service

    @property
    def entity_name(self) -> str:
        return self.service.entity_type.__name__

    def editable_entity_fields_names(self) -> list[str]:
        return [name
            for name in self.service.entity_type.__dataclass_fields__
            if name not  in self.not_editable_fields
        ]
