from abc import abstractmethod
from datetime import datetime
import os


class BaseLogger:
    def __init__(self):
        self.rec = None

    @abstractmethod
    def save_log(self):
        raise NotImplementedError
