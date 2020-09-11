from abc import ABC, abstractmethod

from . import registry


class Module(ABC):
    @property
    @abstractmethod
    def ID(self):
        pass

    @property
    @abstractmethod
    def TITLE(self):
        pass

    @property
    def SUBTITLE(self):
        return ''

    @property
    @abstractmethod
    def PICON_URL(self):
        pass

    @abstractmethod
    def on_visible(self):
        pass

    def refresh(self):
        pass

    def get_entries(self):
        return []

    def on_up(self):
        pass

    def on_down(self):
        pass

    def on_select(self, selection_id=None):
        pass

    @abstractmethod
    def on_exit(self):
        pass

    def on_terminate(self):
        pass

    def log(self, message):
        print(f'{self.ID}: {message}.')

    @classmethod
    def register(cls):
        ins = cls()
        registry.register(ins, {
            'id': ins.ID,
            'title': ins.TITLE,
            'subtitle': ins.SUBTITLE,
            'picon': ins.ID,
            'picon_url': ins.PICON_URL
        })
