from abc import abstractmethod
from stride_detector.coverage_database_helper import *


class BasePromptGenerator:
    # Load code, descriptions, summarization LLM in __init__
    # Take coverage in generate_iterative_prompt

    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def generate_initial_prompt(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_iterative_prompt(self, coverage_database: CoverageDatabase) -> str:
        raise NotImplementedError
