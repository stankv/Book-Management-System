from src.actions.base_action import Action, ActionResult


class ExitAction(Action):
    """Action that terminates the application.

    This action sets the stop flag in ActionResult to signal the
    manager to exit the main application loop."""

    def get_name(self) -> str:
        """Get the action name for menu display.

        Returns:
            str: 'exit'"""
        return "exit"

    def get_description(self) -> str:
        """Get a brief description of the action.

        Returns:
            str: 'Exiting action'"""
        return "Exiting action"

    def execute(self) -> ActionResult:
        """Execute the exit action.

        Displays a goodbye message and returns an ActionResult with
        stop=True to terminate the application.

        Returns:
            ActionResult: With stop=True to end the application loop."""
        print("\nExiting the application\n")
        return ActionResult(stop=True)
