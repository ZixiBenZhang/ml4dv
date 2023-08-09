from datetime import datetime
from abc import abstractmethod
from typing import *

from stride_detector.coverage_database_helper import *


class BaseAgent:
    def __init__(self, log_path=''):
        if log_path == '':
            t = datetime.now()
            t = t.strftime('%Y%m%d_%H%M%S')
            self.log_path = f'./logs/{t}.txt'
        else:
            self.log_path = log_path

    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def end_simulation(self, coverage_database: Union[None, CoverageDatabase]):
        raise NotImplementedError

    @abstractmethod
    def generate_next_value(self, coverage_database: Union[None, CoverageDatabase]):
        raise NotImplementedError
