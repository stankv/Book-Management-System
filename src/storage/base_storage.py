from abc import ABC, abstractmethod


class BaseStorage(ABC):
    @abstractmethod
    def load_data(self):
        pass

    @abstractmethod
    def save_data(self, data):
        pass
