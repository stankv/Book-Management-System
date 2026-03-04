from abc import ABC, abstractmethod


class BaseManager(ABC):

    @abstractmethod
    def run(self):
        pass
    