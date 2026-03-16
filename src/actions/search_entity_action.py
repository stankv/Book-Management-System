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

    def _search_by_id(self, search_term: str) -> list:
        """Search by UUID (exact match, unique)"""
        try:
            uuid_id = UUID(search_term)
            entity = self.service.get_by_id(uuid_id)
            return [entity] if entity else []
        except ValueError:
            return []

    def _search_by_isbn(self, search_term: str, entities: list) -> list:
        """Search by ISBN (case-insensitive exact match, unique)"""
        if not search_term:
            return []
        return [e for e in entities if e.isbn.lower() == search_term.lower()]

    def _search_by_title(self, search_term: str, entities: list) -> list:
        """Search by title (case-insensitive substring match)"""
        if not search_term:
            return []
        search_term_lower = search_term.lower()
        return [e for e in entities if search_term_lower in e.title.lower()]

    def _search_by_author(self, search_term: str, entities: list) -> list:
        """Search by author (case-insensitive substring match)"""
        if not search_term:
            return []
        search_term_lower = search_term.lower()
        return [e for e in entities if search_term_lower in e.author.lower()]

    def _get_search_criteria(self) -> tuple[str, str] | None:
        """Display search menu and return (criteria_type, search_term)"""
        print("\nSearch by:")
        print("  1. ID (UUID)")
        print("  2. Title")
        print("  3. Author")
        print("  4. ISBN")

        choice = input("Select search criteria (1-4): ").strip()

        criteria_map = {
            "1": "id",
            "2": "title",
            "3": "author",
            "4": "isbn"
        }

        if choice not in criteria_map:
            print("Invalid choice. Please select 1-4.")
            return None

        criteria = criteria_map[choice]

        search_term = input(f"Enter {criteria} to search for: ").strip()
        if not search_term:
            print(f"No {criteria} provided. Search cancelled.")
            return None

        return criteria, search_term

    def execute(self) -> ActionResult:
        print(f"\nSearch {self.entity_name}")

        # Получаем критерии поиска
        criteria_result = self._get_search_criteria()
        if not criteria_result:
            return ActionResult()

        criteria, search_term = criteria_result

        # Получаем все книги для поиска (кроме поиска по ID, где используем get_by_id)
        all_entities = self.service.get_all()

        if not all_entities:
            print("No entities found in storage")
            return ActionResult()

        # Выполняем поиск по выбранному критерию
        results = []
        if criteria == "id":
            results = self._search_by_id(search_term)
        else:
            if criteria == "isbn":
                results = self._search_by_isbn(search_term, all_entities)
            elif criteria == "title":
                results = self._search_by_title(search_term, all_entities)
            elif criteria == "author":
                results = self._search_by_author(search_term, all_entities)

        # Выводим результаты
        if not results:
            print(f"No {self.entity_name} found matching {criteria} '{search_term}'")
        else:
            print(f"\nFound {len(results)} {self.entity_name}(s):")
            for entity in results:
                print(f"- [{entity.id}] {entity}")

        return ActionResult()
