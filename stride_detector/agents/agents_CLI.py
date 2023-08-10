from stride_detector.agents.agent_base import *
from stride_detector.stimuli_extractor import *


class CLIAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.i = 0
        self.stimuli = input('Please enter stimuli list:\n')
        self.stimuli = list(map(int, self.stimuli[1:-1].split(',')))

    def end_simulation(self, dut_state: Union[None, DUTState], coverage_database):
        return self.i >= len(self.stimuli)

    def reset(self):
        self.i = 0

    def generate_next_value(self, dut_state: Union[None, DUTState], coverage_database):
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

    def end_simulation(self, dut_state: Union[None, DUTState], coverage_database):
        if self.i >= len(self.stimuli):
            coverage = get_coverage_plan(coverage_database)
            print({k: v for (k, v) in coverage.items() if v > 0}, '\n')
            self._request_input()
        return self.done

    def reset(self):
        self.i = 0
        self.stimuli.clear()

    def generate_next_value(self, dut_state: Union[None, DUTState], coverage_database):
        self.i += 1
        return self.stimuli[self.i - 1] if len(self.stimuli) else 0
