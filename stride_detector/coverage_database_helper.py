from typing import *

from shared_types import CoverageDatabase


def get_coverage_plan(coverage_database: CoverageDatabase) -> Dict[str, int]:
    coverage_plan = {}

    for i, bin_val in enumerate(coverage_database.stride_1_seen):
        if i >= 16:
            i -= 32
        coverage_plan[f'single_{i}'] = bin_val

    for i, bins in enumerate(coverage_database.stride_2_seen):
        for j, bin_val in enumerate(bins):
            if i != j:
                if i >= 16:
                    i -= 32
                if j >= 16:
                    j -= 32
                coverage_plan[f'double_{i}_{j}'] = bin_val

    coverage_plan = {**coverage_plan, **coverage_database.misc_bins}
    return coverage_plan


def get_coverage_rate(coverage_database: CoverageDatabase) -> Tuple[int, int]:
    coverage = get_coverage_plan(coverage_database)
    coverage_hit = {k: v for (k, v) in coverage if v > 0}
    return len(coverage_hit), len(coverage)
