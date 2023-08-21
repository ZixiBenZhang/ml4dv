import numpy as np
from prompt_generators.prompt_generator_base import *
from abc import ABC

BOUND = 523


class TemplatePromptGenerator(BasePromptGenerator, ABC):
    def __init__(self,
                 dut_code_path: str,
                 tb_code_path: str,
                 bin_descr_path: str,
                 code_summary_type: int = 0,  # 0: no code, 1: code, 2: summary
                 sampling_missed_bins: bool = True,
                 ):
        super().__init__()
        self.prev_coverage = (0, -1)
        self.code_summary_type = code_summary_type
        self.sampling_missed_bins = sampling_missed_bins

        self.intro = self._load_introduction()
        self.code_summary = self._load_code_summary(dut_code_path, tb_code_path)
        self.tb_summary = self._load_bins_summary(bin_descr_path)
        self.init_question = self._load_init_question()

        self.coverage_difference_prompts_dict = self._load_coverage_difference_prompts_dict()

    def reset(self):
        self.prev_coverage = (0, -1)

    @abstractmethod
    def _load_introduction(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_code_summary(self, dut_code_dir, tb_code_dir) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_bins_summary(self, bin_descr_dir) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_init_question(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_result_summary(self, **kwargs) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_coverage_difference_prompts_dict(self) -> Dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def _load_iter_question(self, **kwargs) -> str:
        raise NotImplementedError

    # Should be overriden
    def generate_system_prompt(self) -> str:
        return "Please output (positive or negative) a list of integers only, " \
               f"each integer between -{BOUND} and {BOUND}. \n" \
               f"Output format: [a, b, c, ...]."

    def generate_initial_prompt(self) -> str:
        # Initial Template: introduction + summaries + question
        initial_prompt = self.intro + \
                         '\n----------\n' + \
                         self.code_summary + \
                         self.tb_summary + \
                         '\n----------\n' + \
                         self.init_question
        return initial_prompt

    def generate_iterative_prompt(self, coverage_database: GlobalCoverageDatabase, **kwargs) -> str:
        # Iterative Template: result summary + difference + question
        cur_coverage = coverage_database.get_coverage_rate()
        kwargs['no_new_hit'] = cur_coverage == self.prev_coverage

        # calculate difference
        coverage_difference = ""
        coverage_plan = coverage_database.get_coverage_plan()
        missed_bins = list(map(lambda p: p[0], filter(lambda p: p[1] == 0, coverage_plan.items())))
        if len(missed_bins) == 0:
            pass
        # Sampling missed bins
        if self.sampling_missed_bins:
            missed_bins = self._sample_missed_bins(missed_bins, coverage_database.get_coverage_rate())

        for bin_name in missed_bins:
            coverage_difference += self.coverage_difference_prompts_dict[bin_name]

        iterative_prompt = \
            self._load_result_summary(**kwargs) + \
            '------\n' \
            'UNREACHED BINS\n' + \
            coverage_difference + \
            '------\n' + \
            self._load_iter_question(**kwargs)

        self.prev_coverage = cur_coverage
        return iterative_prompt

    @staticmethod
    def _sample_missed_bins(missed_bins: List[str], coverage_rate: Tuple[int, int]) -> List[str]:
        # ORIGINAL
        # if len(missed_bins) >= 40:
        #     missed_bins = np.concatenate([missed_bins[:2],
        #                                   np.random.choice(missed_bins[2:min(25, len(missed_bins))],
        #                                                    3, replace=False),
        #                                   np.random.choice(missed_bins[25:], 2, replace=False)])
        # elif len(missed_bins) >= 5:
        #     missed_bins = np.concatenate([missed_bins[:2],
        #                                   np.random.choice(missed_bins[2:], 3, replace=False)])
        # else:
        #     np.random.shuffle(missed_bins)

        # NEWEST
        if len(missed_bins) >= 40:
            if coverage_rate[0] / coverage_rate[1] <= 1 / 20:  # easier bins
                missed_bins = np.concatenate([missed_bins[:2],
                                              np.random.choice(missed_bins[2:25], 3, replace=False),
                                              np.random.choice(missed_bins[25:], 2, replace=False)])
            else:  # harder bins
                missed_bins = np.concatenate([missed_bins[:2],
                                              np.random.choice(missed_bins[2:], 5, replace=False)])
        elif len(missed_bins) > 7:
            missed_bins = np.concatenate([missed_bins[:2],
                                          np.random.choice(missed_bins[2:], 5, replace=False)])
        else:
            np.random.shuffle(missed_bins)

        # # RANDOM
        # if len(missed_bins) >= 40:
        #     missed_bins = np.random.choice(missed_bins, 7, replace=False)
        # elif len(missed_bins) >= 5:
        #     missed_bins = np.random.choice(missed_bins, 5, replace=False)
        # else:
        #     np.random.shuffle(missed_bins)

        # missed_bins = np.random.choice(missed_bins[:50], 5, replace=False)

        # missed_bins = missed_bins[:min(5, len(missed_bins))]

        return missed_bins
