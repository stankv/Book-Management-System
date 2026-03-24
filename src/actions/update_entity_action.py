import logging

from uuid import UUID

from src.actions import ActionResult
from src.actions.search_entity_action import SearchEntityAction
from src.exceptions import (
    EntityNotFoundError,
    StorageWriteError,
    ActionCancelledError,
    BookValidationError,
)
from src.services.validation_service import ValidationService


log = logging.getLogger(__name__)


class UpdateEntityAction(SearchEntityAction):
    """Action that updates an existing entity.

    Extends SearchEntityAction to first find an entity, then guides the
    user through updating its fields. Only fields that the user chooses
    to modify are updated; others retain their original values.

    This action demonstrates inheritance from another action to reuse
    search functionality while adding update-specific behavior."""

    def get_name(self) -> str:
        """Get the action name for menu display.

        Returns:
            str: 'Update {entity_name}' (e.g., 'Update Book')"""

        return f"Update {self.entity_name}"

    def get_description(self) -> str:
        """Get a brief description of the action.

        Returns:
            str: 'Find and update a {entity_name}'"""

        return f"Find and update a {self.entity_name}"

    def _get_field_value(
        self, field_name: str, current_value, field_type: type, is_required: bool = False
    ) -> tuple[bool, any]:
        """
        Prompt user for a new field value with error handling.

        Args:
            field_name: Name of the field being updated.
            current_value: The current value of the field.
            field_type: The expected type of the field.
            is_required: Whether the field is required.

        Returns:
            tuple[bool, any]: (changed, new_value)

        Raises:
            ActionCancelledError: If user types 'cancel' or presses Ctrl+C.
        """
        try:
            # Display current value
            current_display = current_value if current_value is not None else "(empty)"
            prompt = f"{field_name}"
            if is_required:
                prompt += " (required)"
            prompt += f" [{current_display}]: "

            user_input = input(prompt).strip()

            # If user just pressed Enter, keep current value
            if not user_input:
                return False, current_value

            # Allow user to cancel
            if user_input.lower() == "cancel":
                raise ActionCancelledError("Update cancelled")

            # Type conversion and validation
            try:
                if field_type is int:
                    new_value = int(user_input)
                    # Additional validation for year
                    if field_name == "year":
                        ValidationService.validate_year(new_value, field_name, for_update=True)

                elif field_type == UUID:
                    new_value = UUID(user_input)
                elif field_type is bool:
                    new_value = user_input.lower() in ("true", "yes", "1", "y", "да")
                elif field_type is float:
                    new_value = float(user_input)
                else:  # str and others
                    # Additional validation for ISBN
                    if field_name == "isbn" and user_input:
                        ValidationService.validate_isbn(user_input, field_name)

                    # Check required fields
                    if is_required and not user_input:
                        raise BookValidationError(field_name, f"{field_name} cannot be empty")
                    new_value = user_input

                return True, new_value

            except ValueError:
                print(f"✗ Invalid format for {field_name}. Expected {field_type.__name__}")
                return False, current_value

        except KeyboardInterrupt:
            raise ActionCancelledError("Update aborted by user")

    def _get_editable_fields(self) -> list[tuple[str, type]]:
        """Get list of editable fields with their types.

        Retrieves field names from the base class and pairs them with
        their corresponding types from the entity's dataclass definition.

        Returns:
            list[tuple[str, type]]: List of (field_name, field_type) pairs
                                   for all editable fields."""

        try:
            editable_fields = []
            entity_type = self.service.entity_type

            for field_name in self.editable_entity_fields_names():
                try:
                    field_type = entity_type.__dataclass_fields__[field_name].type
                    editable_fields.append((field_name, field_type))
                except KeyError:
                    log.warning("Field %s not found in entity definition", field_name)
                    continue

            return editable_fields

        except Exception as e:
            log.error("Error getting editable fields: %s", e)
            return []

    def _select_entity_from_results(self, results: list) -> any:
        """Let user select an entity from multiple search results.

        When a search returns multiple entities, this method displays
        them with numbers and lets the user choose which one to update.

        Args:
            results: List of entity objects from search.

        Returns:
            any: The selected entity object.

        Raises:
            ActionCancelledError: If user cancels the selection."""

        try:
            print(f"\nFound {len(results)} {self.entity_name}(s):")
            for idx, entity in enumerate(results, start=1):
                print(f"{idx}. [{entity.id}] {entity}")

            while True:
                choice = input(
                    f"\nSelect a {self.entity_name} to update (1-{len(results)}): "
                ).strip()

                if not choice:
                    raise ActionCancelledError("Selection canceled")

                if choice.lower() == "cancel":
                    raise ActionCancelledError("Update cancelled")

                if not choice.isdigit():
                    print("Please enter the number")
                    continue

                idx = int(choice)
                if idx < 1 or idx > len(results):
                    print(f"Please enter a number between 1 and {len(results)}")
                    continue

                return results[idx - 1]

        except KeyboardInterrupt:
            raise ActionCancelledError("Selection aborted by user")

    def execute(self) -> ActionResult:
        """Execute the update action.

        This method orchestrates the entire update process:
        1. Search for entities using criteria from user
        2. If multiple found, let user select one
        3. For each editable field, prompt for new value
        4. Show changes and ask for confirmation
        5. Apply updates if confirmed

        Returns:
            ActionResult: With error=True if an exception occurred.

        Handles:
            ActionCancelledError: User cancelled at any step.
            EntityNotFoundError: Entity disappeared between search and update.
            StorageWriteError: Save failures.
            KeyboardInterrupt: User pressed Ctrl+C."""

        print(f"\n✏️ Update {self.entity_name}")

        try:
            # Step 1: Search for the book to update
            print(f"Find a {self.entity_name} to update:")
            criteria = self._get_search_criteria()

            if not criteria:
                return ActionResult()

            # Perform search
            try:
                results = self.service.search(**criteria)
            except Exception as e:
                log.error("Search failed: %s", e)
                print(f"✗ Search Error: {e}")
                return ActionResult(error=True)

            if not results:
                field, value = list(criteria.items())[0]
                display_value = str(value) if isinstance(value, UUID) else value
                print(f"✗ {self.entity_name} by {field} '{display_value}' not found")
                return ActionResult()

            # Select entity to update
            entity_to_update = None
            if len(results) == 1:
                entity_to_update = results[0]
                print(f"\nFound {self.entity_name}: {entity_to_update}")
            else:
                entity_to_update = self._select_entity_from_results(results)
                if not entity_to_update:
                    return ActionResult()

            # Step 2: Update fields
            updates = {}
            changes_made = False

            editable_fields = self._get_editable_fields()
            if not editable_fields:
                print("No fields to update")
                return ActionResult()

            print(f"\nUpdate {self.entity_name}. Press Enter to skip the field.")
            print("To cancel all updating, enter 'cancel'")

            for field_name, field_type in editable_fields:
                try:
                    current_value = getattr(entity_to_update, field_name)
                    changed, new_value = self._get_field_value(
                        field_name, current_value, field_type
                    )

                    if changed:
                        updates[field_name] = new_value
                        changes_made = True
                except ActionCancelledError:
                    # Propagate cancellation
                    raise
                except Exception as e:
                    log.error("Error processing field %s: %s", field_name, e)
                    print(f"Error processing field {field_name}: {e}")
                    continue

            # Step 3: Apply updates if any changes were made
            if not changes_made:
                print("\nℹ️ No changes made")
                return ActionResult()

            # Show changes and confirm
            print("\n📋 The following changes will be made:")
            for field, new_value in updates.items():
                old_value = getattr(entity_to_update, field)
                print(f"  {field}: {old_value} → {new_value}")

            try:
                confirm = input("\nApply changes? (y/n): ").strip().lower()
                if confirm != "y":
                    print("ℹ️ Update cancelled")
                    return ActionResult()
            except KeyboardInterrupt:
                raise ActionCancelledError("Update aborted by user")

            # Perform update
            try:
                updated_entity = self.service.update(entity_to_update.id, **updates)

                if updated_entity:
                    print(f"\n✓ {self.entity_name} updated successfully:")
                    print(f"  {updated_entity}")
                else:
                    print(f"\n✗ Failed to update {self.entity_name}")
                    return ActionResult(error=True)

            except EntityNotFoundError as e:
                print(f"✗ {e}")
                return ActionResult(error=True)
            except StorageWriteError as e:
                print(f"✗ Error saving: {e}")
                return ActionResult(error=True)

        except ActionCancelledError as e:
            print(f"ℹ️ {e}")
            return ActionResult()
        except KeyboardInterrupt:
            print("\nℹ️ Update aborted by user")
            return ActionResult()
        except Exception as e:
            log.error("Unexpected error in update action: %s", e)
            print(f"✗ Unexpected error: {e}")
            return ActionResult(error=True)

        return ActionResult()
