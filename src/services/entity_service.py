import logging
import json
from dataclasses import asdict
from uuid import UUID

from src.models.base_entity import BaseEntity
from src.services.base_service import BaseService
from src.storage.base_storage import BaseStorage
from src.exceptions import (
    StorageReadError,
    StorageWriteError,
    StorageCorruptedError,
    EntityNotFoundError,
    EntityValidationError,
    EntityAlreadyExistsError,
)

log = logging.getLogger(__name__)


class EntityService(BaseService):
    """Generic service implementation for managing any entity type.

    Provides concrete implementation of BaseService with common CRUD operations,
    data caching, and error handling. This service works with any entity class
    that inherits from BaseEntity.

    The service uses lazy loading: data is only loaded from storage when first
    accessed. It maintains an in-memory cache (_entities_data) to avoid
    repeated file reads.

    Attributes:
        entity_type: The class of the entity this service manages.
        storage: The storage backend for persistence.
        _entities_data: Internal cache mapping entity IDs to entity objects."""

    def __init__(self, entity_type: type[BaseEntity], storage: BaseStorage):
        """Initialize the entity service.

        Args:
            entity_type: The class of the entity (e.g., Book).
            storage: Storage implementation for persistence."""
        self.entity_type = entity_type
        self.storage = storage
        self._entities_data = {}

    def _load_entities(self):
        """Load entities from storage with comprehensive error handling.

        Reads data from storage, converts UUID strings back to UUID objects,
        and instantiates entity objects. Handles various error conditions
        gracefully, logging issues and continuing with valid data.

        Raises:
            StorageCorruptedError: If JSON parsing fails.
            StorageReadError: For permission or other file access issues.

        Logs:
            - Info: When no entities are found.
            - Error: For each entity that fails to load.
            - Info: Count of successfully recovered entities."""
        try:
            entities = self.storage.load_data()
            if not entities:
                log.info("No entities found in storage")
                return

            loaded_count = 0
            for entity_data in entities:
                try:
                    if "id" not in entity_data:
                        log.error("Entity data missing 'id' field: %s", entity_data)
                        continue

                    entity_data["id"] = UUID(entity_data["id"])
                    entity = self.entity_type(**entity_data)
                    self._entities_data[entity.id] = entity
                    loaded_count += 1
                except (ValueError, TypeError, KeyError) as e:
                    log.error("Failed to load entity %s: %s", entity_data.get("id", "unknown"), e)
                    continue

            log.info("Recovered %d entities from storage", loaded_count)

        except json.JSONDecodeError as e:
            log.error("Failed to parse storage file: %s", e)
            raise StorageCorruptedError(f"JSON parsing error: {e}") from e
        except PermissionError as e:
            log.error("Permission denied accessing storage: %s", e)
            raise StorageReadError(f"Permission denied to read file: {e}") from e
        except Exception as e:
            log.error("Unexpected error loading entities: %s", e)
            raise StorageReadError(f"Unexpected loading error: {e}") from e

    def _save_entities(self):
        """Save entities to storage with error handling.

        Converts all cached entities to dictionaries and writes them
        to storage. Handles various error conditions appropriately.

        Raises:
            StorageWriteError: For permission issues or JSON encoding errors.

        Logs:
            - Debug: Success count on successful save.
            - Error: For various error conditions."""
        try:
            data = [asdict(entity) for entity in self.entities]
            self.storage.save_data(data)
            log.debug("Successfully saved %d entities", len(data))
        except PermissionError as e:
            log.error("Permission denied saving storage: %s", e)
            raise StorageWriteError(f"Permission denied to write to file: {e}") from e
        except (json.JSONDecodeError, TypeError) as e:
            log.error("Failed to encode entities to JSON: %s", e)
            raise StorageWriteError(f"JSON encoding error: {e}") from e
        except Exception as e:
            log.error("Unexpected error saving entities: %s", e)
            raise StorageWriteError(f"Unexpected save error: {e}") from e

    @property
    def entities_data(self):
        """Get the entity cache, loading from storage if necessary.

        Provides lazy loading: if cache is empty, triggers load from storage.

        Returns:
            dict: Dictionary mapping entity IDs to entity objects."""
        if not self._entities_data:
            self._load_entities()
        return self._entities_data

    @property
    def entities(self):
        """Get list of all entities, loading from storage if necessary.

        Provides lazy loading: if cache is empty, triggers load from storage.

        Returns:
            list: List of all entity objects."""
        if not self._entities_data:
            self._load_entities()
        return list(self._entities_data.values())

    def get_all(self):
        """Get all entities.

        Returns:
            list: A list of all entity objects."""
        return self.entities

    def get_by_id(self, id):
        """Get entity by ID.

        Args:
            id: The UUID of the entity to retrieve.

        Returns:
            BaseEntity: The entity object.

        Raises:
            EntityNotFoundError: If no entity exists with the given ID."""
        entity = self.entities_data.get(id)
        if not entity:
            raise EntityNotFoundError(self.entity_type.__name__, id)
        return entity

    def add(self, item):
        """Add a new entity.

        Args:
            item: The entity object to add.

        Returns:
            BaseEntity: The added entity.

        Raises:
            EntityValidationError: If the entity has no ID.
            EntityAlreadyExistsError: If an entity with the same ID already exists.
            StorageWriteError: If saving fails."""

        # Validate item has required fields
        if not hasattr(item, "id") or item.id is None:
            raise EntityValidationError(self.entity_type.__name__, "id", "Entity must have an ID")

        # Check if entity with same ID already exists
        if item.id in self.entities_data:
            raise EntityAlreadyExistsError(self.entity_type.__name__, f"ID {item.id}")

        self.entities_data[item.id] = item
        self._save_entities()
        log.info("Added %s %s: %s", self.entity_type.__name__, item.id, item)
        return item

    def delete(self, id):
        """Delete entity by ID.

        Args:
            id: The UUID of the entity to delete.

        Returns:
            bool: True if deletion was successful.

        Raises:
            EntityNotFoundError: If no entity exists with the given ID.
            StorageWriteError: If saving after deletion fails.D"""
        if id not in self.entities_data:
            raise EntityNotFoundError(self.entity_type.__name__, id)

        self.entities_data.pop(id)
        self._save_entities()
        log.info("Deleted %s %s", self.entity_type.__name__, id)
        return True

    def search(self, **kwargs):
        """Search entities with flexible matching.

        Performs case-insensitive partial matching for string fields,
        exact matching for other types. Empty or None search criteria
        are ignored. Handles errors gracefully, logging warnings and
        continuing with remaining entities.

        Args:
            **kwargs: Field-value pairs to search for.
                     Example: search(title="clean", author="martin")

        Returns:
            list: List of entities matching all criteria.

        Logs:
            - Info: Search results count.
            - Warning: For any errors during entity comparison."""
        if not self.entities:
            return []

        results = []
        for entity in self.entities:
            try:
                match = True
                for field, value in kwargs.items():
                    if value is None or (isinstance(value, str) and not value.strip()):
                        continue

                    entity_value = getattr(entity, field, None)
                    if entity_value is None:
                        match = False
                        break

                    # Handle different types safely
                    if isinstance(entity_value, UUID) and isinstance(value, UUID):
                        if entity_value != value:
                            match = False
                            break
                    elif isinstance(entity_value, str) and isinstance(value, str):
                        if value.lower() not in entity_value.lower():
                            match = False
                            break
                    else:
                        try:
                            if entity_value != value:
                                match = False
                                break
                        except Exception:
                            # If comparison fails, assume no match
                            match = False
                            break

                if match:
                    results.append(entity)
            except Exception as e:
                log.warning("Error comparing entity %s: %s", getattr(entity, "id", "unknown"), e)
                continue

        log.info(
            "Search for %s with criteria %s found %d results",
            self.entity_type.__name__,
            kwargs,
            len(results),
        )
        return results

    def update(self, id, **kwargs):
        """Update entity fields with error handling.

        Updates only the fields specified in kwargs. Compares values before
        updating to avoid unnecessary writes. Only saves to storage if
        changes were actually made.

        Args:
            id: The UUID of the entity to update.
            **kwargs: Field-value pairs to update.

        Returns:
            BaseEntity: The updated entity.

        Raises:
            EntityNotFoundError: If no entity exists with the given ID.
            EntityValidationError: If updating a field fails.
            StorageWriteError: If saving changes fails.

        Logs:
            - Debug: For each updated field.
            - Info: When entity is updated or no changes were made."""

        entity = self.get_by_id(id)  # Will raise EntityNotFoundError if not found

        changes_made = False

        for field, value in kwargs.items():
            if not hasattr(entity, field):
                log.warning("Field %s does not exist in %s", field, self.entity_type.__name__)
                continue

            try:
                current_value = getattr(entity, field)

                # Checking if it is safe to compare values
                try:
                    # Trying to compare values
                    values_are_different = value != current_value
                except Exception as e:
                    # If the comparison fails (different types, not supported, etc.),
                    # we believe that the values are different and need to be updated, but we log the warning
                    log.warning(
                        "Could not compare values for field %s: %s. Will update anyway.", field, e
                    )
                    values_are_different = True

                if values_are_different:
                    try:
                        setattr(entity, field, value)
                        changes_made = True
                        log.debug("Updated %s.%s", self.entity_type.__name__, field)
                    except Exception as e:
                        log.error("Failed to set field %s: %s", field, e)
                        raise EntityValidationError(
                            self.entity_type.__name__, field, f"Cannot set value: {e}"
                        ) from e

            except Exception as e:
                log.error("Failed to update field %s: %s", field, e)
                raise EntityValidationError(self.entity_type.__name__, field, str(e)) from e

        if changes_made:
            self._save_entities()
            log.info("Updated %s %s", self.entity_type.__name__, id)
        else:
            log.info("No changes made to %s %s", self.entity_type.__name__, id)

        return entity
