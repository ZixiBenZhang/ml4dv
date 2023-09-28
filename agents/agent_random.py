from agents.agent_base import *
import random


class RandomAgent(BaseAgent):
    def __init__(self, total_cycle=1000000, seed=0):
        super().__init__()
        self.seed = seed
        random.seed(self.seed)
        self.total_cycle = total_cycle
        self.current_cycle = 0

    def end_simulation(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ):
        return not self.current_cycle < self.total_cycle

    def reset(self):
        self.current_cycle = 0

    def generate_next_value(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ):
        if self.current_cycle % 10000 == 0:
            print(f"Generated {self.current_cycle} stimuli\n")
        self.current_cycle += 1
        return random.getrandbits(32)


class RandomAgent4IC(RandomAgent):
    def __init__(self, total_cycle=1000000, seed=0):
        super().__init__(total_cycle=1000000, seed=0)

    def generate_next_value(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ):
        addr = hex(int(dut_state.get_pc(), 16) + 4)
        instr = hex(random.getrandbits(32))

        if self.current_cycle % 10000 == 0:
            print(f"Generated {self.current_cycle} stimuli\n")
        self.current_cycle += 1

        return [(addr, instr)]
