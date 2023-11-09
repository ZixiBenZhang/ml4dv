# Copyright Zixi Zhang
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from typing import List, Tuple, Any
from ibex_cpu.instructions import Encoding


class BaseFilter:
    def __call__(self, stimuli: List[int]) -> List[Any]:
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
                and Encoding(p[1]).typed() is not None,
                updates,
            )
        )]
