"""Actions package initialization.

This module re-exports all action classes for convenient imports.
Actions implement the Command pattern and provide the user interface
layer of the application."""

from src.actions.base_action import Action as Action, ActionResult as ActionResult
from src.actions.exit_action import ExitAction as ExitAction
from src.actions.list_entities_action import ListEntitiesAction as ListEntitiesAction
from src.actions.search_entity_action import SearchEntityAction as SearchEntityAction
from src.actions.add_entity_action import AddEntityAction as AddEntityAction
from src.actions.update_entity_action import UpdateEntityAction as UpdateEntityAction
from src.actions.delete_entity_action import DeleteEntityAction as DeleteEntityAction
