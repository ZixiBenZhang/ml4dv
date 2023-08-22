from agents.agent_base import *
from loggers.logger_base import BaseLogger
from loggers.logger_csv import CSVLogger
from loggers.logger_txt import TXTLogger
from models.llm_base import *
from prompt_generators.prompt_generator_base import *
from stimuli_extractor import *
from stimuli_filter import *

DIALOG_BOUND = 650

# threshold for restarting a dialog
EPSILON = 3
PERIOD = 7


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
        self.total_msg_cnt = 0
        self.msg_index = 0  # message index for running
        self.dialog_index = 1  # dialog index for running

        # agent updates loggers' records directly; loggers write to files on save_log
        self.loggers = loggers
        self.log_headers()

        self.history_cov_rate = []
        self.all_history_cov_rate = []

    def reset(self):
        self.log_reset()

        self.dialog_index += 1
        self.msg_index = 0
        self.state = 'INIT'
        self.stimuli_buffer.clear()
        self.stimulus_cnt = 0
        self.history_cov_rate.clear()

        self.prompt_generator.reset()
        self.stimulus_generator.reset()
        self.extractor.reset()

    def end_simulation(self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase):
        if coverage_database.get() is None:
            return False

        coverage = coverage_database.get_coverage_plan()
        missed_bins = list(map(lambda p: p[0], filter(lambda p: p[1] == 0, coverage.items())))
        if len(missed_bins) == 0:
            self.state = 'DONE'
            self.log_append({'role': 'coverage', 'content': coverage})
            self.log_append({'role': 'stop', 'content': 'done'})
            self.save_log()
            return True

        if len(self.all_history_cov_rate) >= 25 and self.all_history_cov_rate[-1] == self.all_history_cov_rate[-25]:
            self.state = 'DONE'
            self.log_append({'role': 'coverage', 'content': coverage})
            self.log_append({'role': 'stop', 'content': 'model converged'})
            self.save_log()
            return True

        if len(self.all_history_cov_rate) >= 50 \
                and self.all_history_cov_rate[-1] - self.all_history_cov_rate[-50] <= 2:
            self.state = 'DONE'
            self.log_append({'role': 'coverage', 'content': coverage})
            self.log_append({'role': 'stop', 'content': 'model converged'})
            self.save_log()
            return True

        if self.total_msg_cnt >= DIALOG_BOUND and len(self.stimuli_buffer) == 0:
            self.state = 'DONE'
            self.log_append({'role': 'coverage', 'content': coverage})
            self.log_append({'role': 'stop', 'content': 'max dialog number'})
            self.save_log()
            return True

        return False

    def _get_next_value_from_buffer(self):
        stimulus = self.stimuli_buffer[0]
        self.stimuli_buffer.pop(0)
        self.stimulus_cnt += 1
        return stimulus

    def generate_next_value(self, dut_state: GlobalDUTState,
                            coverage_database: GlobalCoverageDatabase) -> Union[int, None]:
        if coverage_database.get() is None:
            return 0

        coverage = coverage_database.get_coverage_plan()

        # when not first stimulus & need to generate new response
        if len(self.stimuli_buffer) == 0 and self.state != 'INIT':
            # Log coverage
            self.log_append({'role': 'coverage', 'content': coverage})
            coverage_plan = {k: v for (k, v) in coverage.items() if v > 0}
            print(f"Dialog #{self.dialog_index} Message #{self.msg_index} done, \n"
                  f"Total msg cnt: {self.total_msg_cnt} \n" +
                  (f"Hits: {coverage_plan} \n" if coverage_database.get_coverage_rate()[0] <= 100 else '') +
                  f"Coverage rate: {coverage_database.get_coverage_rate()}")

            # Update best_message of LLM
            if self.msg_index != 1:  # not init
                self.stimulus_generator.update_successful(new_coverage=coverage_database.get_coverage_rate()[0])

            # Restart a dialog if low-efficient (nearly converged)
            self.history_cov_rate.append(coverage_database.get_coverage_rate()[0])
            self.all_history_cov_rate.append(coverage_database.get_coverage_rate()[0])
            if len(self.history_cov_rate) >= 7 and self.history_cov_rate[-1] - self.history_cov_rate[-7] < EPSILON:
                self.reset()
                print("\n>>>>> Agent reset <<<<<\n")
            else:
                self.save_log()
                print("log saved\n")

        f_ = 0  # i.e. gibberish response
        while len(self.stimuli_buffer) == 0:
            if self.total_msg_cnt >= DIALOG_BOUND:
                # return 0 (same as None), so entering end_simulation and stops in next loop
                return 0

            # only for gibberish i.e. looped
            if f_:
                self.log_append({'role': 'coverage', 'content': coverage})
                print(f"Dialog #{self.dialog_index} Message #{self.msg_index} done, \n"
                      f"Total msg cnt: {self.total_msg_cnt} \n"
                      f"Gibberish response")
                # Update best_message of LLM
                if self.msg_index != 1:  # not init
                    self.stimulus_generator.update_successful(new_coverage=coverage_database.get_coverage_rate()[0])
                # Restart a dialog if low-efficient (nearly converged)
                self.history_cov_rate.append(coverage_database.get_coverage_rate()[0])
                self.all_history_cov_rate.append(coverage_database.get_coverage_rate()[0])
                if len(self.history_cov_rate) >= 7 and self.history_cov_rate[-1] - self.history_cov_rate[-7] < EPSILON:
                    self.reset()
                    f_ = 0
                    print("\n>>>>> Agent reset <<<<<\n")
                else:
                    self.save_log()
                    print("log saved\n")

            # Generate prompt
            prompt = ""
            if self.state == 'INIT':
                prompt = self.prompt_generator.generate_initial_prompt()
            elif self.state == 'ITER':
                prompt = self.prompt_generator.generate_iterative_prompt(coverage_database, response_invalid=f_)
            elif self.state == 'DONE':  # should never happen
                prompt = "Thank you."
            self.log_append({'role': 'user', 'content': prompt})

            # Get response
            response = self.stimulus_generator(prompt)
            if self.state == 'ITER':
                self.stimulus_generator.append_successful(prompt={'role': 'user', 'content': prompt},
                                                          response={'role': 'assistant', 'content': response},
                                                          cur_coverage=coverage_database.get_coverage_rate()[0])
            if self.state == 'INIT':
                self.state = 'ITER'

            self.total_msg_cnt += 1
            self.msg_index += 1
            self.log_append({'role': 'assistant', 'content': response})

            gibberish = self._check_gibberish(response)
            if gibberish:
                f_ = 1
                continue

            stimuli = self.stimulus_filter(self.extractor(response))
            self.stimuli_buffer.extend(stimuli)

        return self._get_next_value_from_buffer()

    def _check_gibberish(self, response: str) -> bool:
        stimuli = self.stimulus_filter(self.extractor(response))
        if len(stimuli) == 0:
            return True
        lines = response.split('\n')
        cnt = 0
        prev = -1
        for line in lines:
            if len(line) == 0 and prev == 0:
                cnt += 1
            prev = len(line)
        if cnt >= len(lines) // 2:
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

                logger.logged_msg_index = 0
                logger.logged_dialog_index += 1
                # logger.log[-1].append({'role': 'info',
                #                        'content': {'Prompter': type(self.prompt_generator).__name__,
                #                                    'Generator': str(self.stimulus_generator),
                #                                    'Extractor': type(self.extractor).__name__}})
                # if self.stimulus_generator.system_prompt != "":
                #     logger.log[-1].append({'role': 'system',
                #                            'content': self.stimulus_generator.system_prompt})

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
                    logger.log[-1]['Message #'] = self.msg_index
                    logger.log[-1]['Dialog #'] = self.dialog_index
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
