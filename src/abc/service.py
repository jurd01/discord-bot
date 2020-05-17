from abc import ABC


class Service(ABC):
    def run(self):
        pass

    def shutdown(self):
        pass
