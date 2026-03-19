from src.actions import ActionResult
from src.actions.entity_service_action import EntityServiceAction
from src.exceptions import StorageReadError, StorageCorruptedError


class ListEntitiesAction(EntityServiceAction):
    def get_name(self) -> str:
        return f"List {self.entity_name} items"

    def get_description(self) -> str:
        return f"List all the {self.entity_name} entities"

    def execute(self) -> ActionResult:
        print(f"\n📚 All {self.entity_name}s: ")

        try:
            entities = self.service.get_all()

            if not entities:
                print("📭 No books in the storage")
            else:
                for entity in entities:
                    print(f"  - [{entity.id}] {entity}")
            print()

        except StorageReadError as e:
            print(f"✗ Error data reading: {e}")
            return ActionResult(error=True)
        except StorageCorruptedError as e:
            print(f"✗ Data file is corrupted: {e}")
            return ActionResult(error=True)
        except Exception as e:
            print(f"✗ Unexpected error getting list: {e}")
            return ActionResult(error=True)

        return ActionResult()
