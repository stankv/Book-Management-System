from src.actions import ActionResult
from src.actions.entity_service_action import EntityServiceAction
from src.exceptions import (
    EntityValidationError,
    EntityAlreadyExistsError,
    StorageWriteError,
    ActionCancelledError,
    BookValidationError,
    BookYearError,
    BookISBNError,
)
from src.settings import MIN_PUBLICATION_YEAR, MAX_PUBLICATION_YEAR, ISBN_VALID_LENGTHS


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

    def _validate_field(self, field_name: str, value: str) -> tuple[bool, any]:
        """Validate and convert a field value based on its type.

        Performs type conversion and additional business validation
        for specific fields like year and ISBN.

        Args:
            field_name: Name of the field to validate.
            value: String input from the user.

        Returns:
            tuple[bool, any]: (success, converted_value) where success indicates
                              whether validation passed and converted_value is the
                              type-converted value.

        Raises:
            BookValidationError: For specific book validation failures.
            EntityValidationError: For general entity validation issues."""

        try:
            field_type = self.service.entity_type.__dataclass_fields__[field_name].type

            # Empty value is allowed for optional fields
            if not value:
                return True, None

            # Type conversion with specific validations
            try:
                if field_type == int:
                    int_value = int(value)
                    # Additional validation for year field
                    if field_name == "year":
                        current_year = MAX_PUBLICATION_YEAR
                        if int_value < MIN_PUBLICATION_YEAR or int_value > current_year:
                            raise BookYearError(int_value,
                                                f"The year must be between {MIN_PUBLICATION_YEAR} and {MAX_PUBLICATION_YEAR}")
                    return True, int_value

                elif field_type == float:
                    return True, float(value)

                elif field_type == bool:
                    return True, value.lower() in ('true', 'yes', '1', 'y', 'да')

                else:  # str and others
                    # Additional validation for ISBN
                    if field_name == "isbn" and value:
                        # Simple ISBN validation (can be complicated if necessary)
                        isbn_clean = value.replace('-', '').replace(' ', '')
                        if not isbn_clean.isdigit() or len(isbn_clean) not in ISBN_VALID_LENGTHS:
                            raise BookISBNError(value, "ISBN must be 10 or 13 digits!")
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

            # Collect and validate input
            for field_name in self.editable_entity_fields_names():
                while True:
                    try:
                        value = input(f"{field_name}: ").strip()

                        # Allow user to cancel
                        if value.lower() == 'cancel':
                            raise ActionCancelledError("Add cancelled by user")

                        valid, converted_value = self._validate_field(field_name, value)

                        if valid:
                            new_data[field_name] = converted_value
                            break
                        else:
                            # This shouldn't happen with current validation logic
                            print(f"Please enter a valid value for {field_name}")

                    except BookValidationError as e:
                        print(f"✗ {e}")
                        # Continue loop to let user try again
                    except KeyboardInterrupt:
                        raise ActionCancelledError("User aborted add")

            # Confirm data before saving
            print("\n📋 Data entered:")
            for field, value in new_data.items():
                print(f"  {field}: {value}")

            confirm = input(f"\nDo you want to save the {self.entity_name}? (y/n): ").strip()
            if confirm.lower() != 'y':
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
            print(f"✗ Error saving book: {e}")
            return ActionResult(error=True)
        except KeyboardInterrupt:
            print("\nℹ️ User aborted add")
            return ActionResult()
        except Exception as e:
            print(f"✗ Unexpected Add Error: {e}")
            return ActionResult(error=True)

        return ActionResult()
