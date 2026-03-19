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
    """Manager class for book-related operations.

    This class orchestrates the entire book management subsystem, including:
    - Initializing storage and service layers for books
    - Creating and registering all available actions
    - Running the main interaction loop with menu display
    - Handling user input and dispatching to appropriate actions

    The manager follows a plugin-like architecture where actions are
    defined as a class variable and dynamically instantiated.

    Attributes:
        actions: Class-level tuple of action classes available in this manager.
        running: Boolean flag controlling the main application loop.
        books_storage: JSON storage instance for book data.
        books_service: Entity service instance for book operations.
        prepared_actions: Dictionary mapping action names to action instances."""

    actions: ClassVar[tuple[type[Action], ...]] = (
        ListEntitiesAction,
        SearchEntityAction,
        AddEntityAction,
        UpdateEntityAction,
        DeleteEntityAction,
        ExitAction,
    )
    """Tuple of action classes that this manager supports.
    
    The order determines the menu numbering. Each action class must
    accept a service instance in its constructor."""

    def __init__(self, data_dir: Path):
        """Initialize the book manager with a data directory.

        Sets up storage, service, and prepares all actions.

        Args:
            data_dir: Path to the directory where data files will be stored.
                     The books.json file will be created in this directory."""

        self.running = True
        self.books_storage = JsonStorage(data_dir / "books.json")
        self.books_service = EntityService(entity_type=Book, storage=self.books_storage)

        self.prepared_actions: dict[str, Action] = {}
        self.init_actions()

    def init_actions(self):
        """Initialize all action instances.

        Creates an instance of each action class in the actions tuple,
        passing the books service to each. Also validates that action
        names are unique to prevent conflicts.

        Raises:
            ValueError: If two actions have the same name."""

        for action_cls in self.actions:
            action = action_cls(self.books_service)
            name = action.get_name()

            if name in self.prepared_actions:
                msg = f"Action {name!r} already exist"
                raise ValueError(msg)
            self.prepared_actions[name] = action

    def _display_menu(self):
        """Display the main application menu to the user.

        Prints a formatted menu showing all available actions with
        their numbers, names, and descriptions."""

        print("\nBook Manager menu:")
        print("Choose an option: ")
        for idx, action in enumerate(self.prepared_actions.values(), start=1):
            print(f"{idx}. [{action.get_name()}] >> {action.get_description()}")


    def run(self):
        """Execute the main application loop.

        This method:
        1. Displays the menu
        2. Gets user input (by number or action name)
        3. Locates the corresponding action
        4. Executes the action
        5. Processes the result (stop on exit, error handling)
        6. Repeats until running becomes False

        The loop supports both numeric selection (1, 2, 3...) and
        direct action name input.

        Logs:
            - Info: When manager starts
            - Info: When manager stops"""

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
