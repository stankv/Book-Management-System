import logging
from dataclasses import asdict
from uuid import UUID

from src.models.base_entity import BaseEntity
from src.services.base_service import BaseService
from src.storage.base_storage import BaseStorage

log = logging.getLogger(__name__)

class EntityService(BaseService):
    def __init__(self, entity_type: type[BaseEntity], storage: BaseStorage):
        self.entity_type = entity_type
        self.storage = storage
        self._entities_data = {}

    def _load_entities(self):
        entities = self.storage.load_data()
        if not entities:
            log.warning("No entities found in storage")
            return
        for entity_data in entities:
            entity_data["id"] = UUID(entity_data["id"])
            entity = self.entity_type(**entity_data)
            self._entities_data[entity.id] = entity
        log.info("Recovered %d entities from storage", len(self._entities_data))

    def _save_entities(self):
        data = [asdict(entity) for entity in self.entities]
        self.storage.save_data(data)

    @property
    def entities_data(self):
        if not self._entities_data:
            self._load_entities()
        return self._entities_data

    @property
    def entities(self):
        if not self._entities_data:
            self._load_entities()
        return list(self._entities_data.values())

    def get_all(self):
        return self.entities

    def get_by_id(self, id):
        return self.entities_data.get(id)

    def add(self, item):
        self.entities_data[item.id] = item
        self._save_entities()
        log.info("Added %s %s: %s", self.entity_type.__name__, item.id, item)
        return item

    def delete(self, id):
        if id not in self.entities_data:
            log.warning("No %s found with id %s", self.entity_type.__name__, id)
            return
        self.entities_data.pop(id)
        self._save_entities()
        log.info("Deleted %s %s", self.entity_type.__name__, id)

    def search(self, **kwargs):
        """
        Search entities by various criteria.

        Args:
            **kwargs: Field names and values to search for.
                     Examples:
                     - search(id=some_uuid)  # some_uuid должен быть UUID объектом
                     - search(title="Python")
                     - search(author="Smith", year=2020)

        Returns:
            List of matching entities
        """
        if not self.entities:
            log.warning("No entities found in storage")
            return []

        results = []
        for entity in self.entities:
            match = True
            for field, value in kwargs.items():
                if value is None or (isinstance(value, str) and not value.strip()):
                    continue

                entity_value = getattr(entity, field, None)
                if entity_value is None:
                    match = False
                    break

                # Для UUID объектов сравниваем напрямую (они должны быть равны)
                if isinstance(entity_value, UUID) and isinstance(value, UUID):
                    if entity_value != value:
                        match = False
                        break
                # Case-insensitive string comparison for text fields
                elif isinstance(entity_value, str) and isinstance(value, str):
                    if value.lower() not in entity_value.lower():
                        match = False
                        break
                # Exact match for other types (int, etc.)
                else:
                    if entity_value != value:
                        match = False
                        break

            if match:
                results.append(entity)

        log.info("Search for %s with criteria %s found %d results",
                 self.entity_type.__name__, kwargs, len(results))
        return results
