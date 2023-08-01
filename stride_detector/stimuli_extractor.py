import re


class BaseExtractor:
    def __init__(self):
        pass

    def extract(self, text: str):
        pass


class DumbExtractor(BaseExtractor):
    def __init__(self):
        super().__init__()

    def extract(self, text: str):
        numbers = list(map(int, re.findall(r'(-?\d+)|0x[0-9A-F]+', text, re.I)))
        return numbers
