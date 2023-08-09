from abc import abstractmethod
from typing import *


class BaseLLM:
    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt
        self.temperature = 1
        self.top_p = 1

    @abstractmethod
    def __call__(self, prompt: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def reset(self):
        raise NotImplementedError
