import logging
from pathlib import Path
from typing import ClassVar

from src.actions import (
    Action,
    ActionResult,
    AddEntityAction,
    UpdateEntityAction,
    DeleteEntityAction,
    ExitAction,
    ListEntitiesAction,
    SearchEntityAction,
)
from src.managers.base_manager import BaseManager
from src.models.book import Book
from src.services.entity_service import EntityService
from src.storage.json_storage import JsonStorage

log = logging.getLogger(__name__)


class BookManager(BaseManager):

    actions: ClassVar[tuple[type[Action], ...]] = (
        ListEntitiesAction,
        SearchEntityAction,
        AddEntityAction,
        UpdateEntityAction,
        DeleteEntityAction,
        ExitAction,
    )

    def __init__(self, data_dir: Path):
        self.running = True
        self.books_storage = JsonStorage(data_dir / "books.json")
        self.books_service = EntityService(entity_type=Book, storage=self.books_storage)

        self.prepared_actions: dict[str, Action] = {}
        self.init_actions()

    def init_actions(self):
        for action_cls in self.actions:
            action = action_cls(self.books_service)
            name = action.get_name()

            if name in self.prepared_actions:
                msg = f"Action {name!r} already exist"
                raise ValueError(msg)
            self.prepared_actions[name] = action

    def _display_menu(self):
        print("\nBook Manager menu:")
        print("Choose an option: ")
        for idx, action in enumerate(self.prepared_actions.values(), start=1):
            print(f"{idx}. [{action.get_name()}] >> {action.get_description()}")


    def run(self):
        log.info("Start Book Manager")

        while self.running:
            self._display_menu()

            choice = input("Name the action or choose number: ")
            if choice.isdigit():
                index = int(choice) - 1
                if index < 0 or index >= len(self.prepared_actions):
                    print("Invalid choice number, please try again")
                    continue
                try:
                    action = list(self.prepared_actions.values())[int(choice) - 1]
                except IndexError:
                    print("Invalid choice index, please try again")
                    continue
            else:
                try:
                    action = self.prepared_actions[choice]
                except KeyError:
                    print("Invalid choice name, please try again")
                    continue

            result: ActionResult = action.execute()
            if result.error:
                print("❌")
            if result.stop:
                print("\nStop running Book Manager")
                self.running = False
