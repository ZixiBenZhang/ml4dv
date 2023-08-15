from stride_detector.agents.agent_base import *
from stride_detector.prompt_generators.prompt_generator_base import *
from stride_detector.models.llm_base import *
from stride_detector.stimuli_extractor import *
from stride_detector.stimuli_filter import *
from stride_detector.logging.logger_base import BaseLogger
from stride_detector.logging.logger_txt import TXTLogger
from stride_detector.logging.logger_csv import CSVLogger

DIALOG_BOUND = 20


class LLMAgent(BaseAgent):
    def __init__(self,
                 prompt_generator: BasePromptGenerator,
                 stimulus_generator: BaseLLM,
                 stimulus_extractor: BaseExtractor,
                 stimulus_filter: BaseFilter,
                 loggers: List[BaseLogger]):
        super().__init__()
        self.prompt_generator = prompt_generator
        self.stimulus_generator = stimulus_generator
        self.extractor = stimulus_extractor
        self.stimulus_filter = stimulus_filter

        self.state = 'INIT'  # states: INIT, ITER, DONE
        self.stimuli_buffer = []
        self.stimulus_cnt = 0
        self.dialog_index = 0  # dialog index for running

        # agent updates loggers' records directly; loggers write to files on save_log
        self.loggers = loggers
        self.log_headers()

    def reset(self):
        self.log_reset()

        self.dialog_index = 0
        self.state = 'INIT'
        self.stimuli_buffer = []
        self.stimulus_cnt = 0

        self.prompt_generator.reset()
        self.stimulus_generator.reset()
        self.extractor.reset()

    def end_simulation(self, dut_state: Union[None, DUTState], coverage_database: Union[None, CoverageDatabase]):
        if coverage_database is None:
            return False

        coverage = get_coverage_plan(coverage_database)
        missed_bins = list(map(lambda p: p[0], filter(lambda p: p[1] == 0, coverage.items())))
        if len(missed_bins) == 0:
            self.state = 'DONE'
            self.log_append({'role': 'coverage', 'content': coverage})
            self.log_append({'role': 'stop', 'content': 'done'})
            self.save_log()
            return True

        if self.dialog_index >= DIALOG_BOUND and len(self.stimuli_buffer) == 0:
            coverage = get_coverage_plan(coverage_database)
            self.log_append({'role': 'coverage', 'content': coverage})
            self.log_append({'role': 'stop', 'content': 'max dialog number'})
            self.save_log()
            return True

        return False

    def log_headers(self):
        for logger in self.loggers:
            if isinstance(logger, TXTLogger):
                logger: TXTLogger
                logger.log[-1].append({'role': 'info',
                                       'content': {'Prompter': type(self.prompt_generator).__name__,
                                                   'Generator': str(self.stimulus_generator),
                                                   'Temperature': self.stimulus_generator.temperature,
                                                   'Top_p': self.stimulus_generator.top_p,
                                                   'Extractor': type(self.extractor).__name__}})
                if self.stimulus_generator.system_prompt != "":
                    logger.log[-1].append({'role': 'system',
                                           'content': self.stimulus_generator.system_prompt})

            elif isinstance(logger, CSVLogger):
                logger: CSVLogger
                logger.save_info(['Model', str(self.stimulus_generator),
                                  'SYSTEM', self.stimulus_generator.system_prompt,
                                  'temperature', self.stimulus_generator.temperature,
                                  'top_p', self.stimulus_generator.top_p,
                                  'Prompter', type(self.prompt_generator).__name__,
                                  'Extractor', type(self.extractor).__name__])

    def log_reset(self):
        for logger in self.loggers:
            if isinstance(logger, TXTLogger):
                logger: TXTLogger
                logger.log[-1].append({'role': 'reset'})
                logger.save_log()
                logger.log.append([])
                logger.logged_index = 0
                logger.logged_dialog_index = 0
                logger.log[-1].append({'role': 'info',
                                       'content': {'Prompter': type(self.prompt_generator).__name__,
                                                   'Generator': str(self.stimulus_generator),
                                                   'Extractor': type(self.extractor).__name__}})
                if self.stimulus_generator.system_prompt != "":
                    logger.log[-1].append({'role': 'system',
                                           'content': self.stimulus_generator.system_prompt})

            elif isinstance(logger, CSVLogger):
                logger: CSVLogger
                logger.log[-1]['Action'] = "reset"
                logger.save_log()

    # elements:
    # {role: info, content: [agent_info]},
    # {role: ..., content: ...},
    # {role: coverage, content: [coverage_plan]}
    # {role: stop, content: done | max stimuli number}
    # {role: reset}
    def log_append(self, entry: Dict[str, Union[str, dict]]):
        for logger in self.loggers:
            if isinstance(logger, TXTLogger):
                logger: TXTLogger
                logger.log[-1].append(entry)

            elif isinstance(logger, CSVLogger):
                logger: CSVLogger
                if entry['role'] == 'user':
                    logger.log.append({})
                    logger.log[-1]['USER'] = '"' + entry['content'] + '"'
                    logger.log[-1]['Action'] = "none"
                elif entry['role'] == 'assistant':
                    logger.log[-1]['ASSISTANT'] = '"' + entry['content'] + '"'
                elif entry['role'] == 'coverage':
                    coverage_plan = {k: v for (k, v) in entry['content'].items() if v > 0}
                    logger.log[-1]['Coverage Rate'] = len(coverage_plan)
                    logger.log[-1]['Coverage Plan'] = str(coverage_plan)
                elif entry['role'] == 'stop':
                    logger.log[-1]['Action'] = entry['content']
                elif entry['role'] == 'reset':
                    logger.log[-1]['Action'] = "reset"

    def save_log(self):
        for logger in self.loggers:
            logger.save_log()

    def _get_next_value_from_buffer(self):
        stimulus = self.stimuli_buffer[0]
        self.stimuli_buffer.pop(0)
        self.stimulus_cnt += 1
        return stimulus

    def generate_next_value(self, dut_state: Union[None, DUTState],
                            coverage_database: Union[None, CoverageDatabase]) -> Union[int, None]:
        coverage = get_coverage_plan(coverage_database)

        if len(self.stimuli_buffer) == 0 and self.state != 'INIT':  # not first stimulus
            self.log_append({'role': 'coverage', 'content': coverage})
            coverage_plan = {k: v for (k, v) in coverage.items() if v > 0}
            print(f"Dialog #{self.dialog_index} done, hits: {coverage_plan}")
            self.save_log()

        # TODO: other ways to detect gibberish with numbers
        f_ = 0  # i.e. gibberish response
        while len(self.stimuli_buffer) == 0:
            if self.dialog_index >= DIALOG_BOUND:
                # return None (same as 0), so entering end_simulation and stops in next loop
                return None

            if f_:
                self.log_append({'role': 'coverage', 'content': coverage})
                print(f"Dialog #{self.dialog_index} done, gibberish response")
                self.save_log()

            prompt = ""
            if self.state == 'INIT':
                prompt = self.prompt_generator.generate_initial_prompt()
                self.state = 'ITER'
            elif self.state == 'ITER':
                prompt = self.prompt_generator.generate_iterative_prompt(coverage_database,
                                                                         response_invalid=f_)
            elif self.state == 'DONE':  # should never happen
                prompt = "Thank you."
            self.log_append({'role': 'user', 'content': prompt})

            response = self.stimulus_generator(prompt)
            self.dialog_index += 1
            self.log_append({'role': 'assistant', 'content': response})

            gibberish = self._check_gibberish(response)
            if gibberish:
                f_ = 1
                continue

            stimuli = self.stimulus_filter(self.extractor(response))
            self.stimuli_buffer.extend(stimuli)

        return self._get_next_value_from_buffer()

    # Todo: debug
    def _check_gibberish(self, response: str) -> bool:
        stimuli = self.stimulus_filter(self.extractor(response))
        if len(stimuli) == 0:
            return True
        lines = response.split('\n')
        cnt = 0
        for line in lines:
            if len(line) == 0:
                cnt += 1
        if cnt >= len(lines) // 3 * 2:
            return True
        return False
