import os
import sys
from dataclasses import dataclass
from collections import OrderedDict
from typing import Optional

directory = os.path.dirname(os.path.abspath("__file__"))
sys.path.insert(0, os.path.dirname(directory))
# print(sys.path)

from ibex_cpu.instructions import Instr, Cov


@dataclass
class CoverageDatabase:
    instructions: dict[Instr, dict[Cov, int]]

    def get_coverage_dict(self) -> OrderedDict[str, int]:
        generator = (
            (f"{instr.value}_{cov.value}", num)
            for (instr, covs) in self.instructions.items()
            for (cov, num) in covs.items()
        )
        return OrderedDict(sorted(generator, key=lambda cov: cov[0]))

    def get_coverage_vector(self) -> list[int]:
        return list(self.get_coverage_dict().values())

    def get_coverage_bool_vector(self):
        return list(map(lambda x: 1 if x > 0 else 0,
                        self.get_coverage_vector()))

    def output(self):
        for (instr, covs) in self.instructions.items():
            print(f'{instr.value}:')
            print(
                ' ' * 4,
                ', '.join(f'{cov.value}: {num}' for (cov, num) in covs.items())
            )


@dataclass
class Stimulus:
    insn_mem_updates: list[tuple[int, int]]
    finish: bool


@dataclass
class IbexStateInfo:
    last_pc: Optional[int]
    last_insn: Optional[int]
