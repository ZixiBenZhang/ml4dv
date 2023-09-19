from dataclasses import dataclass, astuple

from cocotb.triggers import ClockCycles, ReadOnly
from shared_types import *

@dataclass
class InstructionInfo:
    mask_bits: int
    match_bits: int
    name: str
    kind: str


riscv_instructions = [
    InstructionInfo(0xfe00707f, 0b0110011, 'add', 'reg-op'),
    InstructionInfo(0xfe00707f, 0b0110011 | (0b0100000 << 25), 'sub', 'reg-op'),
    InstructionInfo(0xfe00707f, 0b0110011 | (0b001 << 12), 'sll', 'reg-op'),
    InstructionInfo(0xfe00707f, 0b0110011 | (0b010 << 12), 'slt', 'reg-op'),
    InstructionInfo(0xfe00707f, 0b0110011 | (0b011 << 12), 'sltu', 'reg-op'),
    InstructionInfo(0xfe00707f, 0b0110011 | (0b100 << 12), 'xor', 'reg-op'),
    InstructionInfo(0xfe00707f, 0b0110011 | (0b101 << 12), 'srl', 'reg-op'),
    InstructionInfo(0xfe00707f, 0b0110011 | (0b101 << 12) | (0b0100000 << 25),
        'sra', 'reg-op'),
    InstructionInfo(0xfe00707f, 0b0110011 | (0b110 << 12), 'or', 'reg-op'),
    InstructionInfo(0xfe00707f, 0b0110011 | (0b111 << 12), 'and', 'reg-op'),
]

class InstructionMonitor:
    def __init__(self, dut):
        self.clk = dut.clk_i
        self.insn_valid = dut.u_top.rvfi_valid
        self.insn_pc = dut.u_top.rvfi_pc_rdata
        self.insn = dut.u_top.rvfi_insn
        self.coverage_db = CoverageDatabase(reg_op_insn_coverage = {})
        self.last_pc = None
        self.last_insn = None

        for insn_info in riscv_instructions:
            if insn_info.kind == 'reg-op':
                self.coverage_db.reg_op_insn_coverage[insn_info.name] = RegOpCoverage(0, 0, 0, 0)
            else:
                assert False, f"Invalid kind in {insn_info}"

    def sample_insn_coverage(self):
        if self.insn_valid.value == 0:
            self.last_pc = None
            self.last_insn = None
            return

        self.last_pc = int(self.insn_pc.value)
        self.last_insn = int(self.insn.value)

        for insn_info in riscv_instructions:
            if (self.insn.value & insn_info.mask_bits) == insn_info.match_bits:
                if (insn_info.kind == "reg-op"):
                    self.coverage_db.reg_op_insn_coverage[insn_info.name].sample(self.insn.value)

                break
