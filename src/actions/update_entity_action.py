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

log = logging.getLogger(__name__)


class UpdateEntityAction(SearchEntityAction):
    def get_name(self) -> str:
        return f"Update {self.entity_name}"

    def get_description(self) -> str:
        return f"Find and update a {self.entity_name}"

    def _get_field_value(self, field_name: str, current_value, field_type: type) -> tuple[bool, any]:
        """Prompt user for new field value with error handling"""
        try:
            # Display current value
            prompt = f"{field_name} [{current_value}]: "
            user_input = input(prompt).strip()

            # If user just pressed Enter, keep current value
            if not user_input:
                return False, current_value

            # Allow user to cancel
            if user_input.lower() == 'cancel':
                raise ActionCancelledError("Update cancelled")

            # Type conversion and validation
            try:
                if field_type == int:
                    new_value = int(user_input)
                    # Additional validation for year
                    if field_name == "year":
                        current_year = 2026
                        if new_value < 1450 or new_value > current_year + 5:
                            raise BookValidationError(
                                field_name,
                                f"The year should be between 1450 and {current_year + 5}"
                            )
                elif field_type == UUID:
                    new_value = UUID(user_input)
                elif field_type == bool:
                    new_value = user_input.lower() in ('true', 'yes', '1', 'y', 'да')
                elif field_type == float:
                    new_value = float(user_input)
                else:  # str and others
                    # Additional validation for ISBN
                    if field_name == "isbn" and user_input:
                        isbn_clean = user_input.replace('-', '').replace(' ', '')
                        if not isbn_clean.isdigit() or len(isbn_clean) not in (10, 13):
                            raise BookValidationError(
                                field_name,
                                "ISBN must be 10 or 13 digits"
                            )
                    new_value = user_input

                return True, new_value

            except ValueError as e:
                print(f"✗ Invalid format for {field_name}. Expected {field_type.__name__}")
                return False, current_value

        except KeyboardInterrupt:
            raise ActionCancelledError("Update aborted by user")

    def _get_editable_fields(self) -> list[tuple[str, type]]:
        """Get list of editable fields with their types"""
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
        """Let user select an entity from multiple results"""
        try:
            print(f"\nFound {len(results)} {self.entity_name}(s):")
            for idx, entity in enumerate(results, start=1):
                print(f"{idx}. [{entity.id}] {entity}")

            while True:
                choice = input(f"\nSelect a {self.entity_name} to update (1-{len(results)}): ").strip()

                if not choice:
                    raise ActionCancelledError("Selection canceled")

                if choice.lower() == 'cancel':
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
                    changed, new_value = self._get_field_value(field_name, current_value, field_type)

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
                if confirm != 'y':
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
