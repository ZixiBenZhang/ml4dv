from typing import *

from stride_detector.shared_types import CoverageDatabase as SDCD
from ibex_decoder.shared_types import CoverageDatabase as IDCD
from stride_detector.shared_types import DUTState as SDDS


class GlobalCoverageDatabase:
    def __init__(self, coverage=None):
        self._coverage_database = None
        self.set(coverage)

    def get(self):
        return self._coverage_database

    def set(self, coverage):
        if self._coverage_database is not None:
            assert isinstance(coverage, type(self._coverage_database)), \
                "New coverage is of different type of self._coverage_database."

        if isinstance(coverage, SDCD):
            self._coverage_database: SDCD
        elif isinstance(coverage, IDCD):
            self._coverage_database: IDCD
        elif coverage is None:
            pass
        else:
            raise TypeError(f"Coverage of type {type(coverage)} is not supported.")

        self._coverage_database = coverage

    def get_coverage_plan(self) -> Dict[str, int]:
        if isinstance(self._coverage_database, SDCD):
            return self._get_coverage_plan_SD()
        elif isinstance(self._coverage_database, IDCD):
            return self._get_coverage_plan_ID()
        else:
            raise TypeError(f"coverage_database of type {type(self._coverage_database)} not supported.")

    def _get_coverage_plan_SD(self) -> Dict[str, int]:
        coverage_plan = {}
        for i, bin_val in enumerate(self._coverage_database.stride_1_seen):
            if i >= 16:
                i -= 32
            coverage_plan[f'single_{i}'] = bin_val
        for i, bins in enumerate(self._coverage_database.stride_2_seen):
            for j, bin_val in enumerate(bins):
                if i >= 16:
                    i -= 32
                if j >= 16:
                    j -= 32
                if i == j:
                    continue
                coverage_plan[f'double_{i}_{j}'] = bin_val
        coverage_plan = {**coverage_plan, **self._coverage_database.misc_bins}
        return coverage_plan

    def _get_coverage_plan_ID(self) -> Dict[str, int]:
        # TODO: get_coverage_plan for Ibex Decoder
        pass

    def get_coverage_rate(self) -> Tuple[int, int]:
        coverage = self.get_coverage_plan()
        coverage_hit = {k: v for (k, v) in coverage.items() if v > 0}
        return len(coverage_hit), len(coverage)


class GlobalDUTState:
    def __init__(self):
        self._dut_state = None

    def get(self):
        return self._dut_state

    def set(self, dut_state):
        if self._dut_state is not None:
            assert isinstance(dut_state, type(self._dut_state)), \
                "New dut_state is of different type of self._dut_state."

        if isinstance(dut_state, SDDS):
            self._dut_state: SDDS
        elif dut_state is None:
            pass
        else:
            raise TypeError(f"DUT state of type {type(dut_state)} is not supported.")

        self._dut_state = dut_state

