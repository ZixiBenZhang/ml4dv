from typing import List, Tuple


class BaseFilter:
    def __call__(self, stimuli: List[int]) -> List[int]:
        raise NotImplementedError


class Filter(BaseFilter):
    def __init__(self, lower_bound: int, upper_bound: int):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def __call__(self, stimuli: List[int]) -> List[int]:
        return list(
            filter(lambda x: self.lower_bound <= x <= self.upper_bound, stimuli)
        )


class ICFilter(BaseFilter):
    def __init__(self, lower_bound: int, upper_bound: int):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def __call__(self, updates: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
        return [list(
            filter(
                lambda p: self.lower_bound <= p[0] <= self.upper_bound
                and self.lower_bound <= p[1] <= self.upper_bound
                and p[1] != 0,
                updates,
            )
        )]
