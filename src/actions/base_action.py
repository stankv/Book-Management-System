from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ActionResult:
    stop: bool = False
    error: bool = False


class Action(ABC):
    def __init__(self, *args, **kwargs) -> None:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass

    @abstractmethod
    def get_description(self) -> str:
        pass

    def execute(self) -> ActionResult:
        return ActionResult()
