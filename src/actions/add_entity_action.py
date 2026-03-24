from src.actions import ActionResult
from src.actions.entity_service_action import EntityServiceAction
from src.exceptions import (
    EntityValidationError,
    EntityAlreadyExistsError,
    StorageWriteError,
    ActionCancelledError,
    BookValidationError,
)
from src.services.validation_service import ValidationService
from src.settings import REQUIRED_FIELDS


class AddEntityAction(EntityServiceAction):
    """Action that adds a new entity to the system.

    Prompts the user for all editable fields, validates each input,
    confirms the data, and then creates and saves the new entity.
    Provides comprehensive error handling and user feedback."""

    def get_name(self) -> str:
        """Get the action name for menu display.

        Returns:
            str: 'Add {entity_name} items' (e.g., 'Add Book items')"""

        return f"Add {self.entity_name} items"

    def get_description(self) -> str:
        """Get a brief description of the action.

        Returns:
            str: 'Add a new {entity_name} to storage'"""

        return f"Add a new {self.entity_name} to storage"

    def _validate_field(
        self, field_name: str, value: str, is_required: bool = False
    ) -> tuple[bool, any]:
        """
        Validate and convert a field value based on its type.

        Args:
            field_name: Name of the field to validate.
            value: String input from the user.
            is_required: Whether the field is required.

        Returns:
            tuple[bool, any]: (success, converted_value)

        Raises:
            BookValidationError: For specific book validation failures.
            EntityValidationError: For general entity validation issues.
        """
        try:
            # Check required fields
            if is_required and not value:
                raise BookValidationError(field_name, f"{field_name} cannot be empty")

            # Empty value is allowed for optional fields
            if not value:
                return True, None

            field_type = self.service.entity_type.__dataclass_fields__[field_name].type

            # Type conversion with specific validations
            try:
                if field_type is int:
                    int_value = int(value)
                    # Additional validation for year field
                    if field_name == "year":
                        ValidationService.validate_year(int_value, field_name, for_update=False)
                    return True, int_value

                elif field_type is float:
                    return True, float(value)

                elif field_type is bool:
                    return True, value.lower() in ("true", "yes", "1", "y", "да")

                else:  # str and others
                    # Additional validation for ISBN
                    if field_name == "isbn" and value:
                        ValidationService.validate_isbn(value, field_name)
                    return True, value

            except ValueError as e:
                raise BookValidationError(field_name, f"Type expected {field_type.__name__}: {e}")

        except BookValidationError:
            # Re-raise specific book validation errors
            raise
        except Exception as e:
            raise EntityValidationError(self.entity_name, field_name, str(e))

    def execute(self) -> ActionResult:
        """Execute the add action.

        Guides the user through the process of adding a new entity:
        1. Collects and validates input for each editable field
        2. Allows cancellation at any point with 'cancel' or Ctrl+C
        3. Shows entered data for confirmation
        4. Creates and saves the entity
        5. Provides clear success/error feedback

        Returns:
            ActionResult: With error=True if an exception occurred.

        Handles:
            ActionCancelledError: User cancelled the operation.
            EntityAlreadyExistsError: Duplicate entity.
            StorageWriteError: Save failures.
            KeyboardInterrupt: User pressed Ctrl+C.
            BookValidationError: Field validation failures."""

        print(f"\n➕ Add a new {self.entity_name}")

        try:
            new_data = {}

            # Get required fields for this entity type
            required_fields = REQUIRED_FIELDS.get(self.entity_name, [])

            # Collect and validate input
            for field_name in self.editable_entity_fields_names():
                is_required = field_name in required_fields

                while True:
                    try:
                        prompt = f"{field_name}"
                        if is_required:
                            prompt += " (required)"
                        prompt += ": "

                        value = input(prompt).strip()

                        # Allow user to cancel
                        if value.lower() == "cancel":
                            raise ActionCancelledError("Add cancelled by user")

                        valid, converted_value = self._validate_field(
                            field_name, value, is_required
                        )

                        if valid:
                            new_data[field_name] = converted_value
                            break

                    except BookValidationError as e:
                        print(f"✗ {e}")
                        # Continue loop to let user try again
                    except KeyboardInterrupt:
                        raise ActionCancelledError("User aborted add")

            # Confirm data before saving
            print("\n📋 Data entered:")
            for field, value in new_data.items():
                display_value = value if value is not None else "(empty)"
                print(f"  {field}: {display_value}")

            confirm = input(f"\nDo you want to save the {self.entity_name}? (y/n): ").strip()
            if confirm.lower() != "y":
                raise ActionCancelledError("Add cancelled by user")

            # Create and add entity
            new_entity = self.service.entity_type(**new_data)
            self.service.add(new_entity)
            print(f"\n✓ {self.entity_name} successfully added:")
            print(f"  {new_entity}")

        except ActionCancelledError as e:
            print(f"ℹ️ {e}")
            return ActionResult()
        except EntityAlreadyExistsError as e:
            print(f"✗ {e}")
            return ActionResult(error=True)
        except StorageWriteError as e:
            print(f"✗ Error saving {self.entity_name}: {e}")
            return ActionResult(error=True)
        except KeyboardInterrupt:
            print("\nℹ️ User aborted add")
            return ActionResult()
        except Exception as e:
            print(f"✗ Unexpected Add Error: {e}")
            return ActionResult(error=True)

        return ActionResult()
