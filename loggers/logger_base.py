from abc import abstractmethod
from datetime import datetime
import os
from typing import *


class BaseLogger:
    # Loggers' fields are updated by agent directly. Agent calls save_log when writing to the log files
    @abstractmethod
    def save_log(self):
        raise NotImplementedError
