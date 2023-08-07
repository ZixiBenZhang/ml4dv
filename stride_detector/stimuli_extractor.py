import re
from abc import abstractmethod


class BaseExtractor:
    @abstractmethod
    def __call__(self, text: str):
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        raise NotImplementedError


class DumbExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()

    def __call__(self, text: str):
        numbers = list(map(int, re.findall(r'(-?\d+)|0x[\dA-F]+', text, re.I)))
        return numbers

    def reset(self):
        pass
