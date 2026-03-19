import logging
from uuid import UUID

from src.actions import ActionResult
from src.actions.entity_service_action import EntityServiceAction
from src.exceptions import (
    EntityNotFoundError,
    StorageWriteError,
    ActionCancelledError,
    UserInputError,
)

log = logging.getLogger(__name__)


class DeleteEntityAction(EntityServiceAction):
    def get_name(self) -> str:
        return f"Delete {self.entity_name}"

    def get_description(self) -> str:
        return f"Delete {self.entity_name} by id."

    def execute(self) -> ActionResult:
        print(f"\n🗑️ Deleting {self.entity_name}")

        try:
            entity_id_input = input(f"Enter {self.entity_name} ID to delete: ").strip()

            if not entity_id_input:
                raise ActionCancelledError("Deleting cancelled: ID not entered")

            try:
                entity_id = UUID(entity_id_input)
            except ValueError:
                print(f"✗ Invalid UUID format: {entity_id_input}")
                return ActionResult(error=True)

            try:
                # This will raise EntityNotFoundError if not found
                entity = self.service.get_by_id(entity_id)
                print(f"📖 Found Book: {entity}")

            except EntityNotFoundError:
                print(f"✗ {self.entity_name} with ID {entity_id} not found")
                return ActionResult(error=True)

            confirm = input(f"Are you sure you want to delete this {self.entity_name}? (y/n): ").strip()

            if confirm.lower() != "y":
                log.info("Deletion aborted by user")
                print("ℹ️ Deleting cancelled")
                return ActionResult()

            # Perform deletion
            self.service.delete(entity_id)
            print(f"✓ {self.entity_name} with ID {entity_id} successfully deleted")

        except ActionCancelledError as e:
            print(f"ℹ️ {e}")
            return ActionResult()
        except EntityNotFoundError as e:
            print(f"✗ {e}")
            return ActionResult(error=True)
        except StorageWriteError as e:
            log.error("Storage write error during deletion: %s", e)
            print(f"✗ Error saving data after deletion: {e}")
            return ActionResult(error=True)
        except KeyboardInterrupt:
            print("\nℹ️ Deletion aborted by user")
            return ActionResult()
        except Exception as e:
            log.error("Unexpected error during deletion: %s", e)
            print(f"✗ Unexpected error deleting: {e}")
            return ActionResult(error=True)

        return ActionResult()
