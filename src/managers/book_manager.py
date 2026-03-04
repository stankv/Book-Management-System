import logging
from pathlib import Path
from typing import ClassVar

from src.actions.base_action import Action, ActionResult
from src.managers.base_manager import BaseManager
from src.models.book import Book
from src.services.entity_service import EntityService
from src.storage.json_storage import JsonStorage

log = logging.getLogger(__name__)


class ExampleAction(Action):

    def get_name(self) -> str:
        return "Example Action"

    def get_description(self) -> str:
        return "Example Action that does nothing"


class BookManager(BaseManager):

    actions: ClassVar[tuple[type[Action], ...]] = (
        ExampleAction,
        # TODO: exit action
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
        print("Book Manager menu:")
        print("Choose an option: (WIP)")
        for idx, action in enumerate(self.prepared_actions.values(), start=1):
            print(f"{idx}. [{action.get_name()}] >> {action.get_description()}")


    def run(self):
        log.info("Start Book Manager")

        while self.running:
            self._display_menu()

            # option = input("Choose an option (WIP): ")

            #action: Action = Action(self.books_service)
            result: ActionResult = ActionResult(stop=True)
            if result.stop:
                print("\nStop running Book Manager")
                self.running = False
