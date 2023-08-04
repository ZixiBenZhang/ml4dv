import re


class BaseExtractor:
    def __call__(self, text: str):
        raise NotImplementedError


class DumbExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()

    def __call__(self, text: str):
        numbers = list(map(int, re.findall(r'(-?\d+)|0x[\dA-F]+', text, re.I)))
        return numbers
