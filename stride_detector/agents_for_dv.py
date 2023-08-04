import random
from abc import abstractmethod
from pprint import pprint

from shared_types import CoverageDatabase
from typing import Union
from stimuli_extractor import *


def get_coverage_plan(coverage_database: CoverageDatabase):
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


class BaseAgent:
    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def end_simulation(self, coverage_database: Union[None, CoverageDatabase]):
        raise NotImplementedError

    @abstractmethod
    def generate_next_value(self, coverage_database: Union[None, CoverageDatabase]):
        raise NotImplementedError


class RandomAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.seed = 0
        random.seed(self.seed)
        self.total_cycle = 1000000
        self.current_cycle = 0

    def end_simulation(self, coverage_database):
        return not self.current_cycle < self.total_cycle

    def reset(self):
        self.current_cycle = 0

    def generate_next_value(self, coverage_database):
        self.current_cycle += 1
        return random.getrandbits(32)


class CLIAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.i = 0
        self.stimuli = input('Please enter stimuli list:\n')
        self.stimuli = list(map(int, self.stimuli[1:-1].split(',')))

    def end_simulation(self, coverage_database):
        return self.i >= len(self.stimuli)

    def reset(self):
        self.i = 0

    def generate_next_value(self, coverage_database):
        self.i += 1
        return self.stimuli[self.i - 1]


class CLIStringDialogAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.extractor = DumbExtractor()
        self.i = 0
        self.stimuli = []
        self.done = False

    def end_simulation(self, coverage_database):
        if self.i >= len(self.stimuli):
            pprint(get_coverage_plan(coverage_database))
            response = input('Please enter stimuli list:\n')
            if response == '--exit':
                self.done = True
            responses = response
            while not response == '--end':
                response = input('vvv Please enter LLM response vvv\n')
                responses += response
            self.stimuli += self.extractor(responses)
        return self.done

    def reset(self):
        self.i = 0
        self.stimuli.clear()

    def generate_next_value(self, coverage_database):


        self.i += 1
        return self.stimuli[self.i - 1]


class LLMAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.generator = None
        self.extractor = None
        self.state = 'INIT'  # states: INIT, ITER, DONE
        self.stimuli_buffer = []
        self.stimulus_cnt = 0
        self.missed_bins = []

        # Initial Template: introduction + summaries + question
        dut_code = self._load_dut_code()
        bins_description = self._load_bins_description()
        introduction_dut = \
            f"I have a device under test (DUT). Here's the SystemVerilog code of the DUT:\n\n{dut_code}\n"
        introduction_testbench = \
            f"I also have a testbench that tests the DUT. Here's a description of the bins (i.e. test cases)" \
            f" that the testbench cares about:\n\n{bins_description}\n"
        init_question = self._generate_init_question()
        self.initial_prompt = introduction_dut + introduction_testbench + init_question

        # Iterative Template: result summary + difference + question
        self.result_summary = "The values you provided failed to satisfy all the bins. " \
                              "Here are the unreached bins:\n\n"
        self.coverage_difference_prompts = self._generate_coverage_difference_prompts()
        self.iter_question = self._generate_iter_question()

    @abstractmethod
    def _load_dut_code(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_bins_description(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _generate_init_question(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _generate_coverage_difference_prompts(self) -> dict:
        raise NotImplementedError

    @abstractmethod
    def _generate_iter_question(self) -> str:
        raise NotImplementedError

    def reset(self):
        self.state = 'INIT'
        self.stimuli_buffer = []
        self.stimulus_cnt = 0

    def end_simulation(self, coverage_database: Union[None, CoverageDatabase]):
        if coverage_database is None:
            return False
        if self.stimulus_cnt >= 10000:
            return True
        coverage_plan = get_coverage_plan(coverage_database)
        self.missed_bins = list(map(lambda p: p[0], filter(lambda p: p[1] == 0, coverage_plan.items())))
        if len(self.missed_bins) == 0:
            self.state = 'DONE'
            return True

    def _get_next_value_from_buffer(self):
        stimulus = self.stimuli_buffer[0]
        self.stimuli_buffer = self.stimuli_buffer[1:]
        self.stimulus_cnt += 1
        return stimulus

    def _generate_iterative_prompt(self):
        # missed_bins should have been updated by end_simulation
        coverage_difference = ""
        for bin_name in self.missed_bins:
            coverage_difference += self.coverage_difference_prompts[bin_name()]
        return self.result_summary + coverage_difference + '\n' + self.iter_question

    @abstractmethod
    def _query_to_LLM(self, prompt) -> str:
        raise NotImplementedError

    def generate_next_value(self, coverage_database: Union[None, CoverageDatabase]):
        if len(self.stimuli_buffer):
            return self._get_next_value_from_buffer()

        prompt = ""
        if self.state == 'INIT':
            prompt = self.initial_prompt
            self.state = 'ITER'
        elif self.state == 'ITER':
            prompt = self._generate_iterative_prompt()
        elif self.state == 'DONE':  # should never happen
            prompt = "Thank you."

        response = self._query_to_LLM(prompt)

        stimuli = self.extractor(response)
        self.stimuli_buffer.extend(stimuli)

        return self._get_next_value_from_buffer()
