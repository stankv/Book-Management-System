import logging
from uuid import UUID

from src.actions import ActionResult
from src.actions.entity_service_action import EntityServiceAction
from src.exceptions import (
    StorageReadError,
    StorageCorruptedError,
    ActionCancelledError,
    InvalidChoiceError,
)

log = logging.getLogger(__name__)


class SearchEntityAction(EntityServiceAction):
    """Action that searches for entities based on user-specified criteria.

    Provides a menu-driven interface for users to select search criteria
    (ID, title, author, ISBN) and then performs the search using the
    service layer. Displays results in a formatted list.

    This action serves as a base for UpdateEntityAction, which extends
    the search functionality for update operations."""

    def get_name(self) -> str:
        """Get the action name for menu display.

        Returns:
            str: 'Search {entity_name}' (e.g., 'Search Book')"""

        return f"Search {self.entity_name}"

    def get_description(self) -> str:
        """Get a brief description of the action.
        
        Returns:
            str: 'Search for {entity_name} by id, title, author, or ISBN'"""

        return f"Search for {self.entity_name} by id, title, author, or ISBN"

    def _get_search_criteria(self) -> dict | None:
        """Display search menu and collect user's search criteria.

        Presents a numbered menu of search options, gets user input,
        and returns the appropriate criteria dictionary.

        Returns:
            dict | None: Search criteria dictionary with field-value pairs,
                         or None if the operation was cancelled/invalid.

        Raises:
            ActionCancelledError: If user cancels or aborts the operation.
            InvalidChoiceError: If user selects an invalid menu option.

        Example return values:
            {"id": UUID("...")}
            {"title": "Clean Code"}
            {"author": "Martin"}
            {"isbn": "978-3-16-148410-0"}"""

        try:
            print("\nSearch by:")
            print("  1. ID (UUID)")
            print("  2. Title")
            print("  3. Author")
            print("  4. ISBN")

            choice = input("Select search criteria (1-4): ").strip()

            if choice == "1":
                search_term = input("Enter ID (UUID) to search for: ").strip()
                if not search_term:
                    raise ActionCancelledError("ID search canceled: ID not entered")

                try:
                    uuid_obj = UUID(search_term)
                    return {"id": uuid_obj}
                except ValueError:
                    print(f"✗ Invalid UUID format: {search_term}")
                    return None

            elif choice == "2":
                search_term = input("Enter title to search for: ").strip()
                if not search_term:
                    raise ActionCancelledError("Title search canceled: Title not entered")
                return {"title": search_term}

            elif choice == "3":
                search_term = input("Enter author to search for: ").strip()
                if not search_term:
                    raise ActionCancelledError("Author search canceled: Author not entered")
                return {"author": search_term}

            elif choice == "4":
                search_term = input("Enter ISBN to search for: ").strip()
                if not search_term:
                    raise ActionCancelledError("ISBN search canceled: ISBN not entered")
                return {"isbn": search_term}

            else:
                raise InvalidChoiceError(choice, f"Wrong choice: {choice}. Choose 1-4.")

        except KeyboardInterrupt:
            raise ActionCancelledError("Search aborted by user")

    def execute(self) -> ActionResult:
        """Execute the search action.

        Guides the user through selecting search criteria, performs the
        search using the service, and displays the results. Provides
        clear feedback for empty results or errors.

        Returns:
            ActionResult: With error=True if an exception occurred.

        Handles:
            ActionCancelledError: User cancelled the operation.
            InvalidChoiceError: User selected invalid menu option.
            StorageReadError: For general read failures.
            StorageCorruptedError: For corrupted data files.
            Exception: For unexpected errors."""

        print(f"\n🔍 Search {self.entity_name}")

        try:
            # Get search criteria from user
            criteria = self._get_search_criteria()
            if not criteria:
                return ActionResult()

            # Perform search using service
            results = self.service.search(**criteria)

            # Display results
            if not results:
                field, value = list(criteria.items())[0]
                display_value = str(value) if isinstance(value, UUID) else value
                print(f"✗ {self.entity_name} by {field} '{display_value}' not found")

                # Check if any entities exist at all
                try:
                    if not self.service.get_all():
                        print("📭 No Books in the storage")
                except Exception as e:
                    log.warning("Could not check all entities: %s", e)
            else:
                print(f"\n✓ Found {len(results)} {self.entity_name}(s):")
                for entity in results:
                    print(f"  - [{entity.id}] {entity}")

        except ActionCancelledError as e:
            print(f"ℹ️ {e}")
            return ActionResult()
        except InvalidChoiceError as e:
            print(f"✗ {e}")
            return ActionResult()
        except StorageReadError as e:
            log.error("Storage read error during search: %s", e)
            print(f"✗ Error data reading: {e}")
            return ActionResult(error=True)
        except StorageCorruptedError as e:
            log.error("Storage corrupted during search: %s", e)
            print(f"✗ Data file is corrupted: {e}")
            return ActionResult(error=True)
        except Exception as e:
            log.error("Unexpected error during search: %s", e)
            print(f"✗ Unexpected search error: {e}")
            return ActionResult(error=True)

        return ActionResult()
