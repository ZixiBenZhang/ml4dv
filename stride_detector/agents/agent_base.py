from datetime import datetime
from abc import abstractmethod
from typing import *

from stride_detector.coverage_database_helper import *


class BaseAgent:
    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def end_simulation(self, coverage_database: Union[None, CoverageDatabase]):
        raise NotImplementedError

    @abstractmethod
    def generate_next_value(self, coverage_database: Union[None, CoverageDatabase]):
        raise NotImplementedError
