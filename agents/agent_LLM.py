from agents.agent_base import *
from loggers.logger_base import BaseLogger
from loggers.logger_csv import CSVLogger
from loggers.logger_txt import TXTLogger
from models.llm_base import *
from prompt_generators.prompt_generator_base import *
from stimuli_extractor import *
from stimuli_filter import *


# DIALOG_BOUND = 650
#
# # threshold for restarting a dialog
# EPSILON = 3
# PERIOD = 7


class LLMAgent(BaseAgent):
    def __init__(
        self,
        prompt_generator: BasePromptGenerator,
        stimulus_generator: BaseLLM,
        stimulus_extractor: BaseExtractor,
        stimulus_filter: BaseFilter,
        loggers: List[BaseLogger],
        dialog_bound: int = 650,
        rst_plan: Callable[..., bool] = None,
        token_budget: Union[Budget, None] = None,
    ):
        super().__init__()
        self.prompt_generator = prompt_generator
        self.stimulus_generator = stimulus_generator
        self.extractor = stimulus_extractor
        self.stimulus_filter = stimulus_filter

        self.state = "INIT"  # states: INIT, ITER, DONE
        self.stimuli_buffer = []
        self.stimulus_cnt = 0
        self.dialog_bound = dialog_bound
        self.rst_plan: Callable[..., bool] = rst_plan
        self.total_msg_cnt = 0
        self.msg_index = 0  # message index for running
        self.dialog_index = 1  # dialog index for running

        # agent updates loggers' records directly; loggers write to files on save_log
        self.loggers = loggers
        self.log_headers()

        self.history_cov_rate: List[int] = []
        self.all_history_cov_rate = []

        self.token_budget: Union[Budget, None] = token_budget

    def reset(self):
        self.log_reset()

        self.dialog_index += 1
        self.msg_index = 0
        self.state = "INIT"
        self.stimuli_buffer.clear()
        self.stimulus_cnt = 0
        self.history_cov_rate.clear()

        self.prompt_generator.reset()
        self.stimulus_generator.reset()
        self.extractor.reset()

    def end_simulation(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ):
        if coverage_database.get() is None:
            return False

        coverage = coverage_database.get_coverage_plan()
        missed_bins = list(
            map(lambda p: p[0], filter(lambda p: p[1] == 0, coverage.items()))
        )
        if len(missed_bins) == 0:
            self.state = "DONE"
            self.log_append({"role": "coverage", "content": coverage})
            self.log_append({"role": "stop", "content": "done"})
            self.save_log()
            return True

        if self._check_converge():
            self.state = "DONE"
            self.log_append({"role": "coverage", "content": coverage})
            self.log_append({"role": "stop", "content": "model converged"})
            self.save_log()
            return True

        if self.total_msg_cnt >= self.dialog_bound and len(self.stimuli_buffer) == 0:
            self.state = "DONE"
            self.log_append({"role": "coverage", "content": coverage})
            self.log_append({"role": "stop", "content": "max dialog number"})
            self.save_log()
            return True

        if (
            self.token_budget is not None
            and self.token_budget.no_budget()
            and len(self.stimuli_buffer) == 0
        ):
            self.state = "DONE"
            self.log_append({"role": "coverage", "content": coverage})
            self.log_append({"role": "stop", "content": "token budget exceeded"})
            self.save_log()
            return True

        return False

    def _check_converge(self) -> bool:
        return (
            len(self.all_history_cov_rate) >= 25
            and self.all_history_cov_rate[-1] == self.all_history_cov_rate[-25]
            or len(self.all_history_cov_rate) >= 40
            and self.all_history_cov_rate[-1] - self.all_history_cov_rate[-40] <= 2
        )

    def _get_next_value_from_buffer(self):
        stimulus = self.stimuli_buffer[0]
        self.stimuli_buffer.pop(0)
        self.stimulus_cnt += 1
        return stimulus

    def generate_next_value(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ) -> Union[int, List[Tuple[int, int]], None]:

        # if coverage_database.get() is None:
        #     return 0

        # When not first stimulus & need to generate new response
        # log coverage, update coverage of last msg, check need to reset
        if coverage_database.get() is not None and len(self.stimuli_buffer) == 0 and self.state != "INIT":
            coverage = coverage_database.get_coverage_plan()
            # Log coverage
            self.log_append({"role": "coverage", "content": coverage})
            coverage_plan = {k: v for (k, v) in coverage.items() if v > 0}
            print(
                f"Dialog #{self.dialog_index} Message #{self.msg_index} done, \n"
                f"Total msg cnt: {self.total_msg_cnt} \n"
                + (
                    f"Hits: {coverage_plan} \n"
                    if coverage_database.get_coverage_rate()[0] <= 100
                    else ""
                )
                + f"Coverage rate: {coverage_database.get_coverage_rate()}"
            )

            # Update best_message of LLM
            if self.msg_index != 1:  # not init
                self.stimulus_generator.update_successful(
                    new_coverage=coverage_database
                )

            # Restart a dialog if low-efficient (nearly converged)
            self.history_cov_rate.append(coverage_database.get_coverage_rate()[0])
            self.all_history_cov_rate.append(coverage_database.get_coverage_rate()[0])
            if self.rst_plan(self.history_cov_rate, self.all_history_cov_rate):
                self.reset()
                print("\n>>>>> Agent reset <<<<<\n")
            else:
                self.save_log()
                print("log saved\n")

        f_ = 0  # i.e. gibberish response
        while len(self.stimuli_buffer) == 0:
            if (
                self.total_msg_cnt >= self.dialog_bound
                or self._check_converge()
                or self.token_budget is not None
                and self.token_budget.no_budget()
            ):
                # return 0 (same as None), so entering end_simulation and stops in next loop
                return 0

            # If gibberish
            # log coverage, update coverage of last msg, check need to reset
            if f_:
                coverage = coverage_database.get_coverage_plan() if coverage_database.get() is not None else None
                self.log_append({"role": "coverage", "content": coverage})
                print(
                    f"Dialog #{self.dialog_index} Message #{self.msg_index} done, \n"
                    f"Total msg cnt: {self.total_msg_cnt} \n"
                    f"Gibberish response" if f_ == 1 else f"Invalid updates"
                )

                # Update best_message of LLM
                if self.msg_index != 1:  # not init
                    self.stimulus_generator.update_successful(
                        new_coverage=coverage_database
                    )

                # Restart a dialog if low-efficient (nearly converged)
                self.history_cov_rate.append(coverage_database.get_coverage_rate()[0])
                self.all_history_cov_rate.append(
                    coverage_database.get_coverage_rate()[0]
                )
                if self.rst_plan(self.history_cov_rate, self.all_history_cov_rate):
                    self.reset()
                    f_ = 0
                    print("\n>>>>> Agent reset <<<<<\n")
                else:
                    self.save_log()
                    print("log saved\n")

            # Load prompt
            prompt = ""
            if self.state == "INIT":
                prompt = self.prompt_generator.generate_initial_prompt(
                    current_pc=dut_state.get_pc(),
                    last_instr=dut_state.get_last_instr(),
                )
            elif self.state == "ITER":
                prompt = self.prompt_generator.generate_iterative_prompt(
                    coverage_database,
                    # gibbering
                    response_invalid=(f_ == 1),
                    # asking for long response
                    # warmed_up=(
                    #     len(self.history_cov_rate) >= 4
                    #     and self.history_cov_rate[-1] - self.history_cov_rate[-4] >= 50
                    # ),
                    # invalid update
                    update_invalid=(f_ == 2),
                    current_pc=dut_state.get_pc(),
                    last_instr=dut_state.get_last_instr(),
                )
            elif self.state == "DONE":  # should never happen
                prompt = "Thank you."

            # Generate response
            response, (
                input_token_cnt,
                output_token_cnt,
                total_token_cnt,
            ) = self.stimulus_generator(prompt)

            # update best_msgs
            if self.state == "ITER":
                self.stimulus_generator.append_successful(
                    prompt={"role": "user", "content": prompt},
                    response={"role": "assistant", "content": response},
                    cur_coverage=coverage_database,
                )

            if self.state == "INIT":
                self.state = "ITER"
            self.total_msg_cnt += 1
            self.msg_index += 1

            self.log_append(
                {"role": "user", "content": prompt, "token cnt": input_token_cnt}
            )
            self.log_append(
                {
                    "role": "assistant",
                    "content": response,
                    "token cnt": output_token_cnt,
                }
            )

            if self.token_budget is not None:
                self.token_budget.budget -= total_token_cnt

            gibberish = self._check_gibberish(response)
            if gibberish:
                f_ = 1
                continue

            stimuli = self.stimulus_filter(self.extractor(response))

            # TODO: debug
            update_invalid = self._check_update_invalid(response, stimuli)
            if update_invalid:
                f_ = 2
                continue

            self.stimuli_buffer.extend(stimuli)

        return self._get_next_value_from_buffer()

    def _check_gibberish(self, response: str) -> bool:
        stimuli = self.stimulus_filter(self.extractor(response))
        if len(stimuli) == 0:
            return True
        lines = response.split("\n")
        cnt = 0
        prev = -1
        for line in lines:
            if len(line) == 0 and prev == 0:
                cnt += 1
            prev = len(line)
        if cnt > round(len(lines) / 3 * 2):
            return True
        return False

    def _check_update_invalid(self, response: str, stimuli: List[List[Tuple[int, int]]]) -> bool:
        print(f"checking invalid update: response {len(response)}, stimuli[0] {len(stimuli[0])}")
        if not isinstance(self.stimulus_filter, ICFilter):
            return False
        return len(stimuli[0]) == 0 and len(response) > 10

    def log_headers(self):
        for logger in self.loggers:
            if isinstance(logger, TXTLogger):
                logger: TXTLogger
                logger.log[-1].append(
                    {
                        "role": "info",
                        "content": {
                            "Prompter": type(self.prompt_generator).__name__,
                            "Generator": str(self.stimulus_generator),
                            "Temperature": self.stimulus_generator.temperature,
                            "Top_p": self.stimulus_generator.top_p,
                            "Extractor": type(self.extractor).__name__,
                        },
                    }
                )
                if self.stimulus_generator.system_prompt != "":
                    logger.log[-1].append(
                        {
                            "role": "system",
                            "content": self.stimulus_generator.system_prompt,
                        }
                    )

            elif isinstance(logger, CSVLogger):
                logger: CSVLogger
                logger.save_info(
                    [
                        "Model",
                        str(self.stimulus_generator),
                        "SYSTEM",
                        self.stimulus_generator.system_prompt,
                        "temperature",
                        self.stimulus_generator.temperature,
                        "top_p",
                        self.stimulus_generator.top_p,
                        "Prompter",
                        type(self.prompt_generator).__name__,
                        "Extractor",
                        type(self.extractor).__name__,
                    ]
                )

    def log_reset(self):
        for logger in self.loggers:
            if isinstance(logger, TXTLogger):
                logger: TXTLogger
                logger.log[-1].append({"role": "reset"})
                logger.save_log()

                logger.log.append([])
                logger.logged_index = 0

                logger.logged_msg_index = 0
                logger.logged_dialog_index += 1

            elif isinstance(logger, CSVLogger):
                logger: CSVLogger
                logger.log[-1]["Action"] = "reset"
                logger.save_log()

    # elements:
    # {role: info, content: [agent_info]},
    # {role: ..., content: ..., token cnt: ...},
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
                if entry["role"] == "user":
                    logger.log.append({})
                    logger.log[-1]["USER"] = '"' + entry["content"] + '"'
                    logger.log[-1]["Action"] = "none"
                    logger.log[-1]["Input Token Cnt"] = entry["token cnt"]
                elif entry["role"] == "assistant":
                    logger.log[-1]["Message #"] = self.msg_index
                    logger.log[-1]["Dialog #"] = self.dialog_index
                    logger.log[-1]["ASSISTANT"] = '"' + entry["content"] + '"'
                    logger.log[-1]["Output Token Cnt"] = entry["token cnt"]
                    logger.log[-1]["Total Token Cnt"] = (
                        logger.log[-1]["Input Token Cnt"]
                        + logger.log[-1]["Output Token Cnt"]
                    )
                elif entry["role"] == "coverage":
                    coverage_plan = {
                        k: v for (k, v) in entry["content"].items() if v > 0
                    }
                    logger.log[-1]["Coverage Rate"] = len(coverage_plan)
                    logger.log[-1]["Coverage Plan"] = str(coverage_plan)
                elif entry["role"] == "stop":
                    logger.log[-1]["Action"] = entry["content"]
                elif entry["role"] == "reset":
                    logger.log[-1]["Action"] = "reset"

    def save_log(self):
        for logger in self.loggers:
            logger.save_log()


def rst_plan_ORDINARY(cov_hist: List[int], all_cov_hist: List[int]) -> bool:
    epsilon = 3
    period = 7
    return len(cov_hist) >= period and cov_hist[-1] - cov_hist[-period] < epsilon


def rst_plan_FAST(cov_hist: List[int], all_cov_hist: List[int]) -> bool:
    epsilon = 3
    period = 4
    return len(cov_hist) >= period and cov_hist[-1] - cov_hist[-period] < epsilon


def rst_plan_SLOW(cov_hist: List[int], all_cov_hist: List[int]) -> bool:
    epsilon = 3
    period = 10
    return len(cov_hist) >= period and cov_hist[-1] - cov_hist[-period] < epsilon


def rst_plan_IDADAR(cov_hist: List[int], all_cov_hist: List[int]) -> bool:
    epsilon = 3
    if all_cov_hist[-1] < 300:
        period = 4
    else:
        period = 7
    return len(cov_hist) >= period and cov_hist[-1] - cov_hist[-period] < epsilon


def rst_plan_IDAvoidConverge(cov_hist: List[int], all_cov_hist: List[int]) -> bool:
    epsilon = 3
    t = 14
    if len(all_cov_hist) < t:
        period = 7
    elif all_cov_hist[-t] == all_cov_hist[-1]:
        period = 3
    else:
        period = 7
    return len(cov_hist) >= period and cov_hist[-1] - cov_hist[-period] < epsilon


def rst_plan_IDAdaAvoidConverge(cov_hist: List[int], all_cov_hist: List[int]) -> bool:
    epsilon = 3
    t = 15
    if len(all_cov_hist) < t:
        period = 7
    elif all_cov_hist[-1] < 300:
        period = 4
    elif all_cov_hist[-t] == all_cov_hist[-1]:
        period = 4
    else:
        period = 7
    return len(cov_hist) >= period and cov_hist[-1] - cov_hist[-period] < epsilon
