# Copyright Zixi Zhang
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import numpy as np
from prompt_generators.prompt_generator_base import *
from abc import ABC

BOUND = 523


class TemplatePromptGenerator(BasePromptGenerator, ABC):
    def __init__(
        self,
        dut_code_path: str,
        tb_code_path: str,
        bin_descr_path: str,
        code_summary_type: int = 0,  # 0: no code, 1: code, 2: summary
        sampling_missed_bins_method: Union[str, None] = None,
    ):
        super().__init__()
        self.code_summary_type = code_summary_type

        self.prev_coverage = (0, -1)
        self.adas_cov_hist: List[int] = []

        self.sampling_missed_bins_method: Union[Callable, None] = None
        self._resolve_sampling_method(sampling_missed_bins_method)
        self.sampling_missed_bins: bool = self.sampling_missed_bins_method is not None
        self.cur_sampling_method: Union[Callable, None] = None  # for Adaptive Sampling

        self.intro = self._load_introduction()
        self.code_summary = self._load_code_summary(dut_code_path, tb_code_path)
        self.bin_descr_path = bin_descr_path
        self.init_question = self._load_init_question()

        self.coverage_difference_prompts_dict = (
            self._load_coverage_difference_prompts_dict()
        )

    def _resolve_sampling_method(self, sampling_missed_bins_method: Union[str, None]):
        methods = [
            "ORIGINAL",
            "NEWEST",
            "RANDOM",
            "IDNEWEST",
            "IDADAS",
            "IDADANEW",
            "ICNEWEST",
        ]
        method_mapping = {
            "Pure Random Sampling": "RANDOM",
            "Coverpoint Type-based Sampling for prefetcher": "NEWEST",
            "Coverpoint Type-based Sampling for decoder": "IDNEWEST",
            "Mixed Coverpoint Type-based and Pure Random Sampling for decoder": "IDADANEW",
            "Coverpoint Type-based Sampling for cpu": "ICNEWEST",
        }
        if sampling_missed_bins_method in method_mapping:
            sampling_missed_bins_method = method_mapping[sampling_missed_bins_method]
        assert sampling_missed_bins_method.upper() in methods, (
            f"Invalid sampling method {sampling_missed_bins_method}. \\"
            f"Please use one of the following methods: {methods}. \\"
            f"Otherwise please specify one of the following method names: {method_mapping.keys()}. "
        )
        if type(sampling_missed_bins_method) is str:
            if sampling_missed_bins_method.upper() == "ORIGINAL":
                self.sampling_missed_bins_method = (
                    self._sample_missed_bins_ORIGINAL_degraded
                )
            elif sampling_missed_bins_method.upper() == "NEWEST":
                self.sampling_missed_bins_method = (
                    self._sample_missed_bins_Coverpoint_TypeBased_Sampling_prefetcher
                )
            elif sampling_missed_bins_method.upper() == "RANDOM":
                self.sampling_missed_bins_method = self._sample_missed_bins_RANDOM
            elif sampling_missed_bins_method.upper() == "IDNEWEST":
                self.sampling_missed_bins_method = (
                    self._sample_missed_bins_Coverpoint_TypeBased_Sampling_decoder
                )
            elif sampling_missed_bins_method.upper() == "IDADAS":
                self.sampling_missed_bins_method = self._sample_missed_bins_IDADAS
            elif sampling_missed_bins_method.upper() == "IDADANEW":
                self.sampling_missed_bins_method = (
                    self._sample_missed_bins_Mixed_Coverpoint_TypeBased_Random_Sampling_decoder
                )
            elif sampling_missed_bins_method.upper() == "ICNEWEST":
                self.sampling_missed_bins_method = (
                    self._sample_missed_bins_Coverpoint_TypeBased_Sampling_cpu
                )
            else:
                raise ValueError(
                    f"Invalid sampling method {sampling_missed_bins_method}. "
                )
        else:
            self.sampling_missed_bins_method = None

    def reset(self):
        self.prev_coverage = (0, -1)

    @abstractmethod
    def _load_introduction(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_code_summary(self, dut_code_dir, tb_code_dir) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_bins_summary(self, bin_descr_dir, **kwargs) -> str:
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
        return (
            "Please output (positive or negative) a list of integers only, "
            f"each integer between -{BOUND} and {BOUND}. \n"
            f"Output format: [a, b, c, ...]."
        )

    def generate_initial_prompt(self, **kwargs) -> str:
        # Initial Template: introduction + summaries + question
        tb_summary = self._load_bins_summary(self.bin_descr_path, **kwargs)
        initial_prompt = (
            self.intro
            + "\n----------\n"
            + self.code_summary
            + tb_summary
            + "\n----------\n"
            + self.init_question
        )
        return initial_prompt

    def generate_iterative_prompt(
        self, coverage_database: GlobalCoverageDatabase, **kwargs
    ) -> str:
        # Iterative Template: result summary + difference + question
        cur_coverage = coverage_database.get_coverage_rate()
        self.adas_cov_hist.append(cur_coverage[0])
        kwargs["no_new_hit"] = cur_coverage == self.prev_coverage

        # calculate difference
        coverage_difference = ""
        coverage_plan = coverage_database.get_coverage_plan()
        missed_bins = list(
            map(lambda p: p[0], filter(lambda p: p[1] == 0, coverage_plan.items()))
        )
        if len(missed_bins) == 0:
            pass
        # Sampling missed bins
        if self.sampling_missed_bins:
            missed_bins = self.sampling_missed_bins_method(
                missed_bins, coverage_database.get_coverage_rate()
            )

        for bin_name in missed_bins:
            coverage_difference += self.coverage_difference_prompts_dict[bin_name]

        iterative_prompt = self._load_result_summary(
            **kwargs
        ) + "------\n" "UNREACHED BINS\n" + coverage_difference + "------\n" + self._load_iter_question(
            **kwargs
        )

        self.prev_coverage = cur_coverage
        return iterative_prompt

    """Missed-bin sampling methods"""

    @staticmethod
    def _sample_missed_bins_ORIGINAL_degraded(
        missed_bins: List[str], coverage_rate: Tuple[int, int]
    ) -> List[str]:
        # ORIGINAL (degraded)
        if len(missed_bins) >= 40:
            missed_bins = np.concatenate(
                [
                    missed_bins[:2],
                    np.random.choice(
                        missed_bins[2 : min(25, len(missed_bins))], 3, replace=False
                    ),
                    np.random.choice(missed_bins[25:], 2, replace=False),
                ]
            )
        elif len(missed_bins) >= 5:
            missed_bins = np.concatenate(
                [missed_bins[:2], np.random.choice(missed_bins[2:], 3, replace=False)]
            )
        else:
            pass
        return missed_bins

    @staticmethod
    def _sample_missed_bins_Coverpoint_TypeBased_Sampling_prefetcher(
        missed_bins: List[str], coverage_rate: Tuple[int, int]
    ) -> List[str]:
        # NEWEST: Coverpoint Type-based Sampling for prefetcher bins
        if len(missed_bins) >= 40:
            if coverage_rate[0] / coverage_rate[1] <= 1 / 20:  # easier bins
                missed_bins = np.concatenate(
                    [
                        missed_bins[:2],
                        np.random.choice(missed_bins[2:25], 3, replace=False),
                        np.random.choice(missed_bins[25:], 2, replace=False),
                    ]
                )
            else:  # harder bins
                missed_bins = np.concatenate(
                    [
                        missed_bins[:2],
                        np.random.choice(missed_bins[2:], 5, replace=False),
                    ]
                )
        elif len(missed_bins) > 7:
            missed_bins = np.concatenate(
                [missed_bins[:2], np.random.choice(missed_bins[2:], 5, replace=False)]
            )
        else:
            pass
        return missed_bins

    @staticmethod
    def _sample_missed_bins_RANDOM(
        missed_bins: List[str], coverage_rate: Tuple[int, int]
    ) -> List[str]:
        # RANDOM: Pure Random Sampling
        if len(missed_bins) >= 40:
            missed_bins = np.random.choice(missed_bins, 7, replace=False)
        elif len(missed_bins) >= 5:
            missed_bins = np.random.choice(missed_bins, 5, replace=False)
        else:
            pass
        return missed_bins

    @staticmethod
    def _sample_missed_bins_Coverpoint_TypeBased_Sampling_decoder(
        missed_bins: List[str], coverage_rate: Tuple[int, int]
    ) -> List[str]:
        # ID NEWEST: Coverpoint Type-based Sampling for Ibex decoder bins
        if len(missed_bins) >= 40:
            if coverage_rate[0] / coverage_rate[1] <= 1 / 20:  # easier bins
                missed_bins = np.concatenate(
                    [
                        missed_bins[:2],
                        np.random.choice(missed_bins[2:100], 3, replace=False),
                        np.random.choice(missed_bins[100:], 2, replace=False),
                    ]
                )
            else:  # harder bins
                missed_bins = np.concatenate(
                    [
                        missed_bins[:2],
                        np.random.choice(missed_bins[2:], 5, replace=False),
                    ]
                )
        elif len(missed_bins) > 7:
            missed_bins = np.concatenate(
                [missed_bins[:2], np.random.choice(missed_bins[2:], 5, replace=False)]
            )
        else:
            pass
        return missed_bins

    # Can be extended to adapt all tasks
    def _sample_missed_bins_IDADAS(
        self, missed_bins: List[str], coverage_rate: Tuple[int, int]
    ) -> List[str]:
        # ID Adaptive Sampling: switch sampling method when low efficiency
        def sample_determ(_missed_bins):
            return np.concatenate(
                [_missed_bins[:2], np.random.choice(_missed_bins[2:], 5, replace=False)]
            )

        def sample_mild_determ(_missed_bins):
            return np.concatenate(
                [
                    _missed_bins[:2],
                    np.random.choice(_missed_bins[2:100], 3, replace=False),
                    np.random.choice(_missed_bins[100:], 2, replace=False),
                ]
            )

        def sample_random(_missed_bins):
            return np.random.choice(_missed_bins, 7, replace=False)

        epsilon = 3

        def resolve_strategy() -> Callable:
            if self.cur_sampling_method is None:
                return sample_mild_determ
            if len(self.adas_cov_hist) < 4:
                return self.cur_sampling_method
            # print(f"Checking strategy... Current: {self.cur_sampling_method}")
            if self.adas_cov_hist[-1] - self.adas_cov_hist[-4] < epsilon:
                self.adas_cov_hist.clear()
                if self.cur_sampling_method.__name__ == sample_mild_determ.__name__:
                    print("Sampling: mild determ -> determ\n")
                    return sample_determ
                if self.cur_sampling_method.__name__ == sample_random.__name__:
                    print("Sampling: random -> determ\n")
                    return sample_determ
                if self.cur_sampling_method.__name__ == sample_determ.__name__:
                    print("Sampling: determ -> random\n")
                    return sample_random
            else:
                return self.cur_sampling_method

        if coverage_rate[0] <= 10:
            self.cur_sampling_method = sample_mild_determ
        elif len(missed_bins) >= 40:
            self.cur_sampling_method = resolve_strategy()
        elif len(missed_bins) >= 7:
            self.cur_sampling_method = sample_random
        else:
            self.cur_sampling_method = list

        return self.cur_sampling_method(missed_bins)

    def _sample_missed_bins_Mixed_Coverpoint_TypeBased_Random_Sampling_decoder(
        self, missed_bins: List[str], coverage_rate: Tuple[int, int]
    ) -> List[str]:
        # ID Adaptive Newest: Mixed Pure Random & Coverpoint Type-based Sampling for Ibex decoder bins
        if coverage_rate[0] < 300:
            return self._sample_missed_bins_Coverpoint_TypeBased_Sampling_decoder(
                missed_bins, coverage_rate
            )
        else:
            return self._sample_missed_bins_IDADAS(missed_bins, coverage_rate)

    @staticmethod
    def _sample_missed_bins_Coverpoint_TypeBased_Sampling_cpu(
        missed_bins: List[str], coverage_rate: Tuple[int, int]
    ) -> List[str]:
        # IC NEWEST: Coverpoint Type-based Sampling for Ibex CPU bins
        if len(missed_bins) >= 40:
            if coverage_rate[0] / coverage_rate[1] <= 1 / 4:  # easier bins
                missed_bins = np.concatenate(
                    [
                        missed_bins[:2],
                        np.random.choice(missed_bins[2:50], 3, replace=False),
                        np.random.choice(missed_bins[50:], 2, replace=False),
                    ]
                )
            else:  # harder bins
                missed_bins = np.concatenate(
                    [
                        missed_bins[:2],
                        np.random.choice(missed_bins[2:], 5, replace=False),
                    ]
                )
        elif len(missed_bins) > 7:
            missed_bins = np.concatenate(
                [missed_bins[:2], np.random.choice(missed_bins[2:], 5, replace=False)]
            )
        else:
            pass
        return missed_bins
