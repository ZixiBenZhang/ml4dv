from typing import List


class BaseFilter:
    def __call__(self, stimuli: List[int]):
        raise NotImplementedError


class Filter(BaseFilter):
    def __init__(self, lower_bound: int, upper_bound: int):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def __call__(self, stimuli: List[int]):
        return list(
            filter(lambda x: self.lower_bound <= x <= self.upper_bound, stimuli)
        )
