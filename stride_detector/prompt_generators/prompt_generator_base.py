from abc import abstractmethod
from stride_detector.coverage_database_helper import *


class BasePromptGenerator:
    # Load code, descriptions, summarization LLM in __init__
    # Take coverage in generate_iterative_prompt

    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def generate_system_prompt(self) -> str:
        # SYSTEM message: to describe the assistant’s personality, define what the model should and
        # should not answer, and define the format of model responses.
        # In theory, the model always obey the SYSTEM message despite USER messages
        raise NotImplementedError

    @abstractmethod
    def generate_initial_prompt(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def generate_iterative_prompt(self, coverage_database: CoverageDatabase) -> str:
        raise NotImplementedError
