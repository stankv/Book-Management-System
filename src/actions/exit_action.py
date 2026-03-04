from src.actions.base_action import Action, ActionResult


class ExitAction(Action):
    def get_name(self) -> str:
        return "exit"

    def get_description(self) -> str:
        return "Exiting action"

    def execute(self) -> ActionResult:
        print("\nRunning Example Action\n")
        return ActionResult(stop=True)
