from src.actions import ActionResult
from src.actions.entity_service_action import EntityServiceAction


class AddEntityAction(EntityServiceAction):
    def get_name(self) -> str:
        return f"Add {self.entity_name} items"

    def get_description(self) -> str:
        return f"Add a new {self.entity_name} to storage"

    def execute(self) -> ActionResult:
        print("\nAdding new entity")
        new_data = {}
        for field_name in self.editable_entity_fields_names():
            new_data[field_name] = input(f"{field_name}: ").strip()
        new_entity = self.service.entity_type(**new_data)
        self.service.add(new_entity)
        print("Add new entity", new_entity)
        return ActionResult