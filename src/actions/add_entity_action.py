from datetime import datetime

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


class AddEntityAction(EntityServiceAction):
    def get_name(self) -> str:
        return f"Add {self.entity_name} items"

    def get_description(self) -> str:
        return f"Add a new {self.entity_name} to storage"

    def _validate_field(self, field_name: str, value: str) -> tuple[bool, any]:
        """Validate and convert field value based on field type"""
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
                        current_year = datetime.now().year
                        if int_value < 1450 or int_value > current_year:
                            raise BookYearError(int_value,
                                                f"The year must be between 1450 and {current_year}")
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
                        if not isbn_clean.isdigit() or len(isbn_clean) not in (10, 13):
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

            confirm = input("\nDo you want to save the book? (y/n): ").strip()
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
