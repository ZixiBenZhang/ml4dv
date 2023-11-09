# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from shared_types import CoverageDatabase
from instructions import Instr, Encoding


class InstructionMonitor:
    def __init__(self, dut):
        self.clk = dut.clk_i
        self.insn_valid = dut.u_top.rvfi_valid
        self.insn_pc = dut.u_top.rvfi_pc_rdata
        self.insn = dut.u_top.rvfi_insn
        self.coverage_db = CoverageDatabase(instructions={}, cross_coverage={})
        self.last_pc = None
        self.last_insn = None

        for instr in Instr:
            self.coverage_db.instructions[instr] = {
                cov: 0
                for cov in instr.type().coverpoints()
            }
            self.coverage_db.cross_coverage[instr] = {
                (other_instr, cov): 0
                for (other_instr, cov) in instr.type().cross_coverpoints()
            }

    def sample_insn_coverage(self):
        if self.insn_valid.value == 0:
            self.last_pc = None
            self.last_insn = None
            return

        insn = Encoding(self.insn.value).typed()

        if insn is not None:
            mnemonic = insn.instruction()
            for coverpoint in insn.sample_coverage():
                self.coverage_db.instructions[mnemonic][coverpoint] += 1

            if (
                self.last_insn is not None and
                (last_insn := Encoding(self.last_insn.value).typed()) is not None
            ):
                for insn_cov in insn.sample_cross_coverage(last_insn):
                    self.coverage_db.instructions[mnemonic][insn_cov] += 1

        self.last_pc = int(self.insn_pc.value)
        self.last_insn = int(self.insn.value)
