from src.actions import ActionResult
from src.actions.entity_service_action import EntityServiceAction


class ListEntitiesAction(EntityServiceAction):
    def get_name(self) -> str:
        return f"List {self.entity_name} items"

    def get_description(self) -> str:
        return f"List all the {self.entity_name} entities"

    def execute(self) -> ActionResult:
        print(f"\nAll the {self.entity_name} items: ")
        for entity in self.service.get_all():
            print(f"- [{entity.id}] {entity}")
        print()
        return ActionResult