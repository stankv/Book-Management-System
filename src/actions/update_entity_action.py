import logging
from uuid import UUID

from src.actions import ActionResult
from src.actions.search_entity_action import SearchEntityAction

log = logging.getLogger(__name__)


class UpdateEntityAction(SearchEntityAction):
    def get_name(self) -> str:
        return f"Update {self.entity_name}"

    def get_description(self) -> str:
        return f"Find and update a {self.entity_name}"

    def _get_field_value(self, field_name: str, current_value, field_type: type) -> tuple[bool, any]:
        """
        Prompt user for new field value.
        Returns (changed, new_value)
        """
        # Display current value
        prompt = f"{field_name} [{current_value}]: "
        user_input = input(prompt).strip()

        # If user just pressed Enter, keep current value
        if not user_input:
            return False, current_value

        # Type conversion and validation
        try:
            if field_type == int:
                new_value = int(user_input)
            elif field_type == UUID:
                new_value = UUID(user_input)
            else:  # str and others
                new_value = user_input

            return True, new_value
        except ValueError as e:
            print(f"Invalid input for {field_name}. Expected {field_type.__name__}. Error: {e}")
            return False, current_value

    def _get_editable_fields(self) -> list[tuple[str, type, any]]:
        """
        Get list of editable fields with their types and current values.
        Excludes 'id' field as it's not editable.
        """
        editable_fields = []
        entity_type = self.service.entity_type

        for field_name in self.editable_entity_fields_names():
            field_type = entity_type.__dataclass_fields__[field_name].type
            editable_fields.append((field_name, field_type))

        return editable_fields

    def execute(self) -> ActionResult:
        print(f"\nUpdate {self.entity_name}")

        # Step 1: Search for the book to update
        print(f"First, let's find the {self.entity_name} to update:")
        criteria = self._get_search_criteria()

        if not criteria:
            return ActionResult()

        # Perform search
        results = self.service.search(**criteria)

        if not results:
            field, value = list(criteria.items())[0]
            display_value = str(value) if isinstance(value, UUID) else value
            print(f"No {self.entity_name} found matching {field} '{display_value}'")

            if not self.service.get_all():
                print("No entities found in storage")
            return ActionResult()

        # If multiple results found, let user choose
        entity_to_update = None
        if len(results) == 1:
            entity_to_update = results[0]
            print(f"\nFound one {self.entity_name}:")
        else:
            print(f"\nFound {len(results)} {self.entity_name}(s):")
            for idx, entity in enumerate(results, start=1):
                print(f"{idx}. [{entity.id}] {entity}")

            choice = input(f"\nSelect {self.entity_name} to update (1-{len(results)}): ").strip()

            if not choice.isdigit() or int(choice) < 1 or int(choice) > len(results):
                print("Invalid selection. Update cancelled.")
                return ActionResult()

            entity_to_update = results[int(choice) - 1]

        print(f"\nUpdating {self.entity_name}: {entity_to_update}")

        # Step 2: Update fields
        updates = {}
        changes_made = False

        for field_name, field_type in self._get_editable_fields():
            current_value = getattr(entity_to_update, field_name)
            changed, new_value = self._get_field_value(field_name, current_value, field_type)

            if changed:
                updates[field_name] = new_value
                changes_made = True

        # Step 3: Apply updates if any changes were made
        if not changes_made:
            print("No changes made. Update cancelled.")
            return ActionResult()

        # Confirm update
        print("\nChanges to be made:")
        for field, new_value in updates.items():
            old_value = getattr(entity_to_update, field)
            print(f"  {field}: {old_value} -> {new_value}")

        confirm = input("\nApply these changes? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Update cancelled.")
            return ActionResult()

        # Perform update
        updated_entity = self.service.update(entity_to_update.id, **updates)

        if updated_entity:
            print(f"\n✓ {self.entity_name} successfully updated:")
            print(f"  {updated_entity}")
        else:
            print(f"\n✗ Failed to update {self.entity_name}")

        return ActionResult()
