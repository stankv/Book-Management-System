from src.actions import ActionResult
from src.actions.entity_service_action import EntityServiceAction
from src.exceptions import StorageReadError, StorageCorruptedError


class ListEntitiesAction(EntityServiceAction):
    """Action that displays all entities of a specific type.

    Retrieves all entities from the service and displays them in a
    formatted list. Handles empty collections and various storage errors."""

    def get_name(self) -> str:
        """Get the action name for menu display.

        Returns:
            str: 'List {entity_name} items' (e.g., 'List Book items')"""
        return f"List {self.entity_name} items"

    def get_description(self) -> str:
        """Get a brief description of the action.

        Returns:
            str: 'List all the {entity_name} entities'"""
        return f"List all the {self.entity_name} entities"

    def execute(self) -> ActionResult:
        """Execute the list action.

        Fetches all entities from the service and displays them.
        Shows appropriate messages for empty storage or errors.

        Returns:
            ActionResult: With error=True if an exception occurred.

        Handles:
            StorageReadError: For general read failures.
            StorageCorruptedError: For corrupted data files.
            Exception: For unexpected errors."""

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
