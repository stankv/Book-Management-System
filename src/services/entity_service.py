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
