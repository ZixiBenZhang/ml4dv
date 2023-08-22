import stride_detector.shared_types
from agents.agent_base import *


class DumbAgent4ID(BaseAgent):
    def __init__(self):
        super().__init__()
        self.i = 0
        # Test instructions
        #  add x1, x2, x3
        #  add x2, x3, x4
        #  add x1, x3, x7
        #
        #  addi x18, x20, 1
        #
        #  xor x1, x2, x3
        #  xor x1, x14, x17
        #
        #  lw x10, 16(x11)
        #  lh x10, 16(x11)
        #  lb x10, 16(x11)
        #
        #  sw x10, 16(x11)
        #  sh x10, 16(x11)
        #  sb x10, 16(x11)
        self.test_instructions = [
            0x003100B3,
            0x00418133,
            0x007180B3,
            0x001A0913,
            0x003140B3,
            0x011740B3,
            0x0105A503,
            0x01059503,
            0x01058503,
            0x00A5A823,
            0x00A59823,
            0x00A58823,
        ]

    def reset(self):
        self.i = 0

    def end_simulation(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ):
        return self.i >= len(self.test_instructions)

    def generate_next_value(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ):
        self.i += 1
        return self.test_instructions[self.i - 1]
