import os
import random
from datetime import datetime

from coverage_database_helper import *
from models.llm_base import BaseLLM
from prompt_generators.prompt_generator_base import BasePromptGenerator
from stimuli_extractor import *
from stimuli_filter import *


class BaseAgent:
    def __init__(self, log_path=''):
        if log_path == '':
            t = datetime.now()
            t = t.strftime('%Y%m%d_%H%M%S')
            self.log_path = f'./logs/{t}.txt'
        else:
            self.log_path = log_path

    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def end_simulation(self, coverage_database: Union[None, CoverageDatabase]):
        raise NotImplementedError

    @abstractmethod
    def generate_next_value(self, coverage_database: Union[None, CoverageDatabase]):
        raise NotImplementedError


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

    def end_simulation(self, coverage_database: Union[None, CoverageDatabase]):
        return not self.current_stride <= self.STRIDE_MAX

    def generate_next_value(self, coverage_database: Union[None, CoverageDatabase]):
        if self.new_value is None:
            self.new_value = 1
            return self.new_value

        if coverage_database.stride_1_seen[self.current_stride] > 16:
            self.current_stride += 1

        return self.new_value + self.current_stride


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
    def __init__(self, stimulus_extractor: BaseExtractor = DumbExtractor()):
        super().__init__()
        self.extractor = stimulus_extractor
        self.i = 0
        self.stimuli = []
        self.done = False

    def _request_input(self):
        response = input('vvv Please enter LLM response vvv\n')
        if response == '--exit':
            self.done = True
            return
        responses = response
        while response != '--end':
            response = input()
            responses += response
        print("\n>>> Here's your prompt <<<")
        print(responses, '\n')
        self.stimuli.extend(self.extractor(responses))
        self.done = False
        return

    def end_simulation(self, coverage_database):
        if self.i >= len(self.stimuli):
            coverage = get_coverage_plan(coverage_database)
            print({k: v for (k, v) in coverage.items() if v > 0}, '\n')
            self._request_input()
        return self.done

    def reset(self):
        self.i = 0
        self.stimuli.clear()

    def generate_next_value(self, coverage_database):
        self.i += 1
        return self.stimuli[self.i - 1] if len(self.stimuli) else 0


class LLMAgent(BaseAgent):
    def __init__(self,
                 prompt_generator: BasePromptGenerator,
                 stimulus_generator: BaseLLM,
                 stimulus_extractor: BaseExtractor,
                 stimulus_filter: BaseFilter,
                 log_path=''):
        super().__init__(log_path)
        self.prompt_generator = prompt_generator
        self.stimulus_generator = stimulus_generator
        self.extractor = stimulus_extractor
        self.stimulus_filter = stimulus_filter

        self.state = 'INIT'  # states: INIT, ITER, DONE
        self.stimuli_buffer = []
        self.stimulus_cnt = 0

        # elements:
        # {role: info, content: [agent_info]},
        # {role: ..., content: ...},
        # {role: coverage, content: [coverage_plan]}
        # {role: stop, content: done | max stimuli number
        self.log: List[List[Dict[str, Union[str, dict]]]] = [[]]
        self.logged_index = 0  # log index for logging
        self.logged_dialog_index = 0  # dialog index for logging
        self.dialog_index = 0  # dialog index for running
        self.log[-1].append({'role': 'info',
                             'content': {'Prompter': type(self.prompt_generator).__name__,
                                         'Generator': str(self.stimulus_generator),
                                         'Extractor': type(self.extractor).__name__}})
        if self.stimulus_generator.system_prompt != "":
            self.log[-1].append({'role': 'system', 'content': self.stimulus_generator.system_prompt})

    def reset(self):
        self.save_log()
        self.log.append([])
        self.logged_index = 0
        self.logged_dialog_index = 0
        self.dialog_index = 0
        self.log[-1].append({'role': 'info',
                             'content': {'Prompter': type(self.prompt_generator).__name__,
                                         'Generator': str(self.stimulus_generator),
                                         'Extractor': type(self.extractor).__name__}})
        if self.stimulus_generator.system_prompt != "":
            self.log[-1].append({'role': 'system', 'content': self.stimulus_generator.system_prompt})

        self.state = 'INIT'
        self.stimuli_buffer = []
        self.stimulus_cnt = 0

        self.prompt_generator.reset()
        self.stimulus_generator.reset()
        self.extractor.reset()

    def end_simulation(self, coverage_database: Union[None, CoverageDatabase]):
        if coverage_database is None:
            return False
        if self.dialog_index >= 20:
            coverage = get_coverage_plan(coverage_database)
            self.log[-1].append({'role': 'coverage', 'content': coverage})
            self.log[-1].append({'role': 'stop', 'content': 'max dialog number'})
            self.save_log()
            return True
        coverage_plan = get_coverage_plan(coverage_database)
        missed_bins = list(map(lambda p: p[0], filter(lambda p: p[1] == 0, coverage_plan.items())))
        if len(missed_bins) == 0:
            self.state = 'DONE'
            coverage = coverage_plan
            self.log[-1].append({'role': 'coverage', 'content': coverage})
            self.log[-1].append({'role': 'stop', 'content': 'done'})
            self.save_log()
            return True
        return False

    def _get_next_value_from_buffer(self):
        stimulus = self.stimuli_buffer[0]
        self.stimuli_buffer.pop(0)
        self.stimulus_cnt += 1
        return stimulus

    def save_log(self):
        if not os.path.exists('./logs'):
            os.makedirs('./logs')
        with open(self.log_path, 'a+') as f:
            while self.logged_index < len(self.log[-1]):
                rec = self.log[-1][self.logged_index]

                if rec['role'] == 'info':
                    agent_info: Dict[str, str] = rec['content']
                    for k, v in agent_info.items():
                        f.write(f'{k}: {v}\n')
                    f.write('\n')

                elif rec['role'] == 'coverage':
                    coverage: Dict[str, int] = rec['content']
                    coverage_plan = {k: v for (k, v) in coverage.items() if v > 0}
                    f.write(f'Coverage rate: {len(coverage_plan)} / {len(coverage)}\n')
                    f.write(f'Coverage plan: {coverage_plan}\n\n')

                elif rec['role'] == 'stop':
                    f.write(f'Done: {rec["content"]}\n')

                else:
                    if rec['role'] == 'user':
                        self.logged_dialog_index += 1
                    f.write(f'Index: {self.logged_dialog_index}\n')
                    f.write(f'Role: {rec["role"]}\n')
                    f.write(f'Content: {rec["content"]}\n\n')

                self.logged_index += 1

    def generate_next_value(self, coverage_database: Union[None, CoverageDatabase]):
        if len(self.stimuli_buffer) == 0 and self.state != 'INIT':  # not first stimulus
            coverage = get_coverage_plan(coverage_database)
            self.log[-1].append({'role': 'coverage', 'content': coverage})

            coverage_plan = {k: v for (k, v) in coverage.items() if v > 0}
            print(f"Dialog #{self.dialog_index} done, hits: {coverage_plan}")

            self.save_log()

        while len(self.stimuli_buffer) == 0:
            prompt = ""
            if self.state == 'INIT':
                prompt = self.prompt_generator.generate_initial_prompt()
                self.state = 'ITER'
            elif self.state == 'ITER':
                prompt = self.prompt_generator.generate_iterative_prompt(coverage_database)
            elif self.state == 'DONE':  # should never happen
                prompt = "Thank you."
            self.log[-1].append({'role': 'user', 'content': prompt})

            response = self.stimulus_generator(prompt)
            self.dialog_index += 1
            self.log[-1].append({'role': 'assistant', 'content': response})

            stimuli = self.stimulus_filter(self.extractor(response))
            self.stimuli_buffer.extend(stimuli)

            self.save_log()

        return self._get_next_value_from_buffer()
