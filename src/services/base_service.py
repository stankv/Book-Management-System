from abc import ABC, abstractmethod


class BaseService(ABC):
    @abstractmethod
    def get_all(self):
        pass

    @abstractmethod
    def get_by_id(self, id):
        pass

    @abstractmethod
    def add(self, item):
        pass

    @abstractmethod
    def delete(self, id):
        pass
