import re
from typing import *

from stride_detector.shared_types import CoverageDatabase as SDCD
from ibex_decoder.shared_types import CoverageDatabase as IDCD
from stride_detector.shared_types import DUTState as SDDS
from ibex_cpu.shared_types import IbexStateInfo as ICDS
from ibex_cpu.shared_types import CoverageDatabase as ICCD


class GlobalCoverageDatabase:
    def __init__(self, coverage=None):
        self._coverage_database = None
        self.set(coverage)

    def get(self):
        return self._coverage_database

    def set(self, coverage):
        if self._coverage_database is not None:
            assert isinstance(
                coverage, type(self._coverage_database)
            ), "New coverage is of different type of self._coverage_database."

        if isinstance(coverage, SDCD):
            self._coverage_database: SDCD
        elif isinstance(coverage, IDCD):
            self._coverage_database: IDCD
        elif isinstance(coverage, ICCD):
            self._coverage_database: ICCD
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
        elif isinstance(self._coverage_database, ICCD):
            return self._get_coverage_plan_IC()
        else:
            raise TypeError(
                f"coverage_database of type {type(self._coverage_database)} not supported."
            )

    def _get_coverage_plan_SD(self) -> Dict[str, int]:
        coverage_plan = {}
        for i, bin_val in enumerate(self._coverage_database.stride_1_seen):
            if i >= 16:
                i -= 32
            coverage_plan[f"single_{i}"] = bin_val
        for i, bins in enumerate(self._coverage_database.stride_2_seen):
            for j, bin_val in enumerate(bins):
                if i >= 16:
                    i -= 32
                if j >= 16:
                    j -= 32
                if i == j:
                    continue
                coverage_plan[f"double_{i}_{j}"] = bin_val
        coverage_plan = {**coverage_plan, **self._coverage_database.misc_bins}
        return coverage_plan

    def _get_coverage_plan_ID(self) -> Dict[str, int]:
        coverage_plan = {}
        op_bins = ["alu_ops", "alu_imm_ops", "misc", "load_ops", "store_ops"]
        reg_bins = ["read_reg_a", "read_reg_b", "write_reg"]
        cross_bins = [
            "alu_ops_x_read_reg_a",
            "alu_ops_x_read_reg_b",
            "alu_ops_x_write_reg",
            "alu_imm_ops_x_read_reg_a",
            "alu_imm_ops_x_write_reg",
            "load_ops_x_read_reg_a",
            "load_ops_x_write_reg",
            "store_ops_x_read_reg_a",
            "store_ops_x_read_reg_b",
        ]

        for bins_type in op_bins:
            bins: Dict[str, int] = getattr(self._coverage_database, bins_type)
            for op, v in bins.items():
                op = op.upper()
                k = f"{bins_type}_{op}"
                if bins_type == "alu_ops":
                    k = op
                elif bins_type == "alu_imm_ops":
                    k = f"{op}I"
                elif bins_type == "misc":
                    k = "illegal_instruction"
                elif bins_type == "load_ops":
                    k = f"L{op[0]}"
                elif bins_type == "store_ops":
                    k = f"S{op[0]}"
                coverage_plan[k] = v

        for bins_type in reg_bins:
            bins: List[int] = getattr(self._coverage_database, bins_type)
            for i, v in enumerate(bins):
                k = f"{bins_type}_{i}"
                if bins_type == "read_reg_a":
                    k = f"read_A_reg_{i}"
                elif bins_type == "read_reg_b":
                    k = f"read_B_reg_{i}"
                elif bins_type == "write_reg":
                    k = f"write_reg_{i}"
                coverage_plan[k] = v

        for bins_type in cross_bins:
            bins: Dict[str, List[int]] = getattr(self._coverage_database, bins_type)
            for op, regs in bins.items():
                op = op.upper()
                for i, v in enumerate(regs):
                    k = f"{bins_type}__{op}_{i}"
                    if bins_type == "alu_ops_x_read_reg_a":
                        k = f"{op}_x_read_A_reg_{i}"
                    elif bins_type == "alu_ops_x_read_reg_b":
                        k = f"{op}_x_read_B_reg_{i}"
                    elif bins_type == "alu_ops_x_write_reg":
                        k = f"{op}_x_write_reg_{i}"
                    elif bins_type == "alu_imm_ops_x_read_reg_a":
                        k = f"{op}I_x_read_A_reg_{i}"
                    elif bins_type == "alu_imm_ops_x_write_reg":
                        k = f"{op}I_x_write_reg_{i}"
                    elif bins_type == "load_ops_x_read_reg_a":
                        k = f"L{op[0]}_x_read_A_reg_{i}"
                    elif bins_type == "load_ops_x_write_reg":
                        k = f"L{op[0]}_x_write_reg_{i}"
                    elif bins_type == "store_ops_x_read_reg_a":
                        k = f"S{op[0]}_x_read_A_reg_{i}"
                    elif bins_type == "store_ops_x_read_reg_b":
                        k = f"S{op[0]}_x_read_B_reg_{i}"
                    coverage_plan[k] = v

        return coverage_plan

    def _get_coverage_plan_IC(self) -> Dict[str, int]:
        # TODO
        coverage_plan = {}
        op_bins = ["alu_ops", "alu_imm_ops", "misc", "load_ops", "store_ops"]
        reg_bins = ["read_reg_a", "read_reg_b", "write_reg"]
        cross_bins = [
            "alu_ops_x_read_reg_a",
            "alu_ops_x_read_reg_b",
            "alu_ops_x_write_reg",
            "alu_imm_ops_x_read_reg_a",
            "alu_imm_ops_x_write_reg",
            "load_ops_x_read_reg_a",
            "load_ops_x_write_reg",
            "store_ops_x_read_reg_a",
            "store_ops_x_read_reg_b",
        ]

        for bins_type in op_bins:
            bins: Dict[str, int] = getattr(self._coverage_database, bins_type)
            for op, v in bins.items():
                op = op.upper()
                k = f"{bins_type}_{op}"
                if bins_type == "alu_ops":
                    k = op
                elif bins_type == "alu_imm_ops":
                    k = f"{op}I"
                elif bins_type == "misc":
                    k = "illegal_instruction"
                elif bins_type == "load_ops":
                    k = f"L{op[0]}"
                elif bins_type == "store_ops":
                    k = f"S{op[0]}"
                coverage_plan[k] = v

        for bins_type in reg_bins:
            bins: List[int] = getattr(self._coverage_database, bins_type)
            for i, v in enumerate(bins):
                k = f"{bins_type}_{i}"
                if bins_type == "read_reg_a":
                    k = f"read_A_reg_{i}"
                elif bins_type == "read_reg_b":
                    k = f"read_B_reg_{i}"
                elif bins_type == "write_reg":
                    k = f"write_reg_{i}"
                coverage_plan[k] = v

        for bins_type in cross_bins:
            bins: Dict[str, List[int]] = getattr(self._coverage_database, bins_type)
            for op, regs in bins.items():
                op = op.upper()
                for i, v in enumerate(regs):
                    k = f"{bins_type}__{op}_{i}"
                    if bins_type == "alu_ops_x_read_reg_a":
                        k = f"{op}_x_read_A_reg_{i}"
                    elif bins_type == "alu_ops_x_read_reg_b":
                        k = f"{op}_x_read_B_reg_{i}"
                    elif bins_type == "alu_ops_x_write_reg":
                        k = f"{op}_x_write_reg_{i}"
                    elif bins_type == "alu_imm_ops_x_read_reg_a":
                        k = f"{op}I_x_read_A_reg_{i}"
                    elif bins_type == "alu_imm_ops_x_write_reg":
                        k = f"{op}I_x_write_reg_{i}"
                    elif bins_type == "load_ops_x_read_reg_a":
                        k = f"L{op[0]}_x_read_A_reg_{i}"
                    elif bins_type == "load_ops_x_write_reg":
                        k = f"L{op[0]}_x_write_reg_{i}"
                    elif bins_type == "store_ops_x_read_reg_a":
                        k = f"S{op[0]}_x_read_A_reg_{i}"
                    elif bins_type == "store_ops_x_read_reg_b":
                        k = f"S{op[0]}_x_read_B_reg_{i}"
                    coverage_plan[k] = v

        return coverage_plan

    def get_coverage_rate(self) -> Tuple[int, int]:
        coverage = self.get_coverage_plan()
        coverage_hit = {k: v for (k, v) in coverage.items() if v > 0}
        return len(coverage_hit), len(coverage)

    def get_coverage_score(self, prioritise_harder_bins=True) -> float:
        if isinstance(self._coverage_database, SDCD):
            coverage_plan = self._get_coverage_plan_SD()
            coverage = [k for (k, v) in coverage_plan.items() if v > 0]
            if not prioritise_harder_bins:  # without prioritising harder bins
                return len(coverage)
            # Prioritise harder bins
            return sum(
                map(
                    lambda k: 2.5
                    if re.fullmatch(r"double_-?\d+_-?\d+", k) is not None
                    else 1,
                    coverage,
                )
            )
        elif isinstance(self._coverage_database, IDCD):
            coverage_plan = self._get_coverage_plan_ID()
            coverage = [k for (k, v) in coverage_plan.items() if v > 0]
            if not prioritise_harder_bins:  # without prioritising harder bins
                return len(coverage)
            # Prioritise harder bins
            return sum(map(lambda k: 2.5 if "_x_" in k else 1, coverage))
        elif isinstance(self._coverage_database, ICCD):
            coverage_plan = self._get_coverage_plan_ID()
            coverage = [k for (k, v) in coverage_plan.items() if v > 0]
            if not prioritise_harder_bins:  # without prioritising harder bins
                return len(coverage)
            # TODO: Prioritise harder bins
            return sum(map(lambda k: 2.5 if "_x_" in k else 1, coverage))
        else:
            raise TypeError(
                f"coverage_database of type {type(self._coverage_database)} not supported."
            )


class GlobalDUTState:
    def __init__(self):
        self._dut_state = None

    def get(self):
        return self._dut_state

    def set(self, dut_state):
        if self._dut_state is not None:
            assert isinstance(
                dut_state, type(self._dut_state)
            ), "New dut_state is of different type of self._dut_state."

        if isinstance(dut_state, SDDS):
            self._dut_state: SDDS
        elif isinstance(dut_state, ICDS):
            self._dut_state: ICDS
        elif dut_state is None:
            pass
        else:
            raise TypeError(f"DUT state of type {type(dut_state)} is not supported.")

        self._dut_state = dut_state


class Budget:
    budget: int
    init_budget: int
    total_budget: int

    def __init__(self, budget_per_trial, total_budget):
        self.init_budget = budget_per_trial
        self.total_budget = total_budget

    def no_budget(self):
        return self.budget <= 0
