from abc import abstractmethod
from datetime import datetime
import os
from typing import *


class BaseLogger:
    @abstractmethod
    def save_log(self):
        raise NotImplementedError
