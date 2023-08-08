import re
from abc import abstractmethod
import numpy as np


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
        literals = list(filter(lambda x: x[-1] != '.', re.findall(r'0x[\da-fA-F]+|-?\d+[.:]?', text, re.I)))
        numbers = list(map(lambda x: (int(x, 16) if x[:2] == '0x' else int(x)), literals))
        return numbers

    def reset(self):
        pass
