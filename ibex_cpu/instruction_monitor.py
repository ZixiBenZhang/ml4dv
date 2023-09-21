import os
import sys

directory = os.path.dirname(os.path.abspath("__file__"))
sys.path.insert(0, os.path.dirname(directory))
# print(sys.path)

from ibex_cpu.shared_types import CoverageDatabase
from ibex_cpu.instructions import Instr, Encoding


class InstructionMonitor:
    def __init__(self, dut):
        self.clk = dut.clk_i
        self.insn_valid = dut.u_top.rvfi_valid
        self.insn_pc = dut.u_top.rvfi_pc_rdata
        self.insn = dut.u_top.rvfi_insn
        self.coverage_db = CoverageDatabase(instructions={})
        self.last_pc = None
        self.last_insn = None

        for instr in Instr:
            self.coverage_db.instructions[instr] = {
                cov: 0
                for cov in instr.type().coverpoints()
            }

    def sample_insn_coverage(self):
        if self.insn_valid.value == 0:
            self.last_pc = None
            self.last_insn = None
            return

        self.last_pc = int(self.insn_pc.value)
        self.last_insn = int(self.insn.value)

        insn = Encoding(self.insn.value).typed()

        if insn is not None:
            mnemonic = insn.instruction()
            for coverpoint in insn.sample_coverage():
                self.coverage_db.instructions[mnemonic][coverpoint] += 1
