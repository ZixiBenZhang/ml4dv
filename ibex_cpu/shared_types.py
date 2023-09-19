from dataclasses import dataclass, astuple
from typing import Optional
from pprint import pprint

@dataclass
class RegOpCoverage:
    seen: int
    zero_dst: int
    zero_src: int
    same_src: int

    def sample(self, insn_bits):
        self.seen += 1

        rd = (insn_bits >> 7) & 0x1f
        if rd == 0:
            self.zero_dst += 1

        rs1 = (insn_bits >> 15) & 0x1f
        rs2 = (insn_bits >> 20) & 0x1f

        if rs1 == 0 or rs2 == 0:
            self.zero_src += 1

        if rs1 == rs2:
            self.same_src += 1

    def __str__(self):
        return f'seen: {self.seen}, zero_dst: {self.zero_dst}, zero_src: {self.zero_src}, same_src: {self.same_src}'

@dataclass
class CoverageDatabase:
    reg_op_insn_coverage: dict[str, RegOpCoverage]

    def get_coverage_vector(self):
        coverage_list = list(self.reg_op_insn_coverage.items())
        coverage_list.sort(key = lambda c: c[0])
        coverage_vector = []

        for insn_name, coverage_info in coverage_list:
            coverage_vector += list(astuple(coverage_info))

        return coverage_vector

    def get_coverage_bool_vector(self):
        return list(map(lambda x: 1 if x > 0 else 0,
            self.get_coverage_vector()))

    def output(self):
        for insn_name, insn_coverage in self.reg_op_insn_coverage.items():
            print(f'{insn_name} {insn_coverage}')

@dataclass
class Stimulus:
    insn_mem_updates: list[tuple[int, int]]
    finish: bool

@dataclass
class IbexStateInfo:
    last_pc: Optional[int]
    last_insn: Optional[int]
