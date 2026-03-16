import logging
from uuid import UUID

from src.actions import ActionResult
from src.actions.entity_service_action import EntityServiceAction

log = logging.getLogger(__name__)


class SearchEntityAction(EntityServiceAction):
    def get_name(self) -> str:
        return f"Search {self.entity_name}"

    def get_description(self) -> str:
        return f"Search for {self.entity_name} by id, title, author, or ISBN"

    def _get_search_criteria(self) -> dict | None:
        """Display search menu and return search criteria dict"""
        print("\nSearch by:")
        print("  1. ID (UUID)")
        print("  2. Title")
        print("  3. Author")
        print("  4. ISBN")

        choice = input("Select search criteria (1-4): ").strip()

        if choice == "1":
            criteria = "id"
            search_term = input("Enter ID (UUID) to search for: ").strip()
            if not search_term:
                print("No ID provided. Search cancelled.")
                return None

            # Validate UUID format and convert to UUID object
            try:
                uuid_obj = UUID(search_term)
                return {"id": uuid_obj}  # <-- Передаем UUID объект, а не строку
            except ValueError:
                print(f"Invalid UUID format: {search_term}")
                return None

        elif choice == "2":
            search_term = input("Enter title to search for: ").strip()
            if not search_term:
                print("No title provided. Search cancelled.")
                return None
            return {"title": search_term}

        elif choice == "3":
            search_term = input("Enter author to search for: ").strip()
            if not search_term:
                print("No author provided. Search cancelled.")
                return None
            return {"author": search_term}

        elif choice == "4":
            search_term = input("Enter ISBN to search for: ").strip()
            if not search_term:
                print("No ISBN provided. Search cancelled.")
                return None
            return {"isbn": search_term}

        else:
            print("Invalid choice. Please select 1-4.")
            return None

    def execute(self) -> ActionResult:
        print(f"\nSearch {self.entity_name}")

        # Get search criteria from user
        criteria = self._get_search_criteria()
        if not criteria:
            return ActionResult()

        # Perform search using service
        results = self.service.search(**criteria)

        # Display results
        if not results:
            field, value = list(criteria.items())[0]
            # Для красивого отображения UUID в сообщении
            display_value = str(value) if isinstance(value, UUID) else value
            print(f"No {self.entity_name} found matching {field} '{display_value}'")

            # Special message if no entities at all
            if not self.service.get_all():
                print("No entities found in storage")
        else:
            print(f"\nFound {len(results)} {self.entity_name}(s):")
            for entity in results:
                print(f"- [{entity.id}] {entity}")

        return ActionResult()
