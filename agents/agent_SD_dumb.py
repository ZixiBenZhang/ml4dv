import stride_detector.shared_types
from agents.agent_base import *


class DumbAgent4SD(BaseAgent):
    def __init__(self):
        super().__init__()
        self.current_stride = 1
        self.new_value = None
        self.NUM_STRIDES = 32
        self.STRIDE_MIN = -16
        self.STRIDE_MAX = 15

    def reset(self):
        self.new_value = None
        self.current_stride = 1

    def end_simulation(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ):
        return not self.current_stride <= self.STRIDE_MAX

    def generate_next_value(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ):
        if self.new_value is None:
            self.new_value = 1
            return self.new_value

        coverage_database_ = coverage_database.get()
        assert coverage_database_ is stride_detector.shared_types.CoverageDatabase

        if coverage_database_.stride_1_seen[self.current_stride] > 16:
            self.current_stride += 1

        return self.new_value + self.current_stride
