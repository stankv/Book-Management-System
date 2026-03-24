from abc import ABC
from typing import ClassVar

from src.actions import Action
from src.services.entity_service import EntityService


class EntityServiceAction(Action, ABC):
    """Base class for actions that operate on entities via a service.

    Provides common functionality for actions that work with a specific
    entity type through an EntityService. This includes determining the
    entity name and listing editable fields.

    Attributes:
        service: The EntityService instance for the specific entity type.
        not_editable_fields: Class-level set of field names that cannot be
                            edited by the user (e.g., 'id')."""

    not_editable_fields: ClassVar[frozenset[str]] = frozenset(
        {
            "id",
        },
    )
    """Set of field names that should not be editable by users.
    
    These fields are automatically excluded from operations that modify
    entities, such as add and update actions. By default, 'id' is
    considered non-editable as it's system-generated."""

    def __init__(self, service: EntityService):
        """Initialize the action with a service.

        Args:
            service: The EntityService instance for the target entity type."""
        super().__init__()
        self.service = service

    @property
    def entity_name(self) -> str:
        """Get the name of the entity type this action works with.

        Returns:
            str: The class name of the entity (e.g., 'Book')."""
        return self.service.entity_type.__name__

    def editable_entity_fields_names(self) -> list[str]:
        """Get list of field names that can be edited by users.

        Filters out fields that are in the not_editable_fields set.

        Returns:
            list[str]: Names of fields that users can modify."""
        return [
            name
            for name in self.service.entity_type.__dataclass_fields__
            if name not in self.not_editable_fields
        ]
