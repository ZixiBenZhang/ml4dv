from stride_detector.prompt_generators.prompt_generator_base import *
from abc import ABC


class TemplatePromptGenerator(BasePromptGenerator, ABC):
    def __init__(self, dut_code_path: str, bin_descr_path: str):
        self.intro = self._load_introduction()
        self.dut_summary = self._load_dut_summary(dut_code_path)
        self.tb_summary = self._load_testbench_summary(bin_descr_path)
        self.init_question = self._load_init_question()

        self.res_summary = self._load_result_summary()
        self.coverage_difference_prompts_dict = self._load_coverage_difference_prompts_dict()
        self.iter_question = self._load_iter_question()

    def reset(self):
        pass

    @abstractmethod
    def _load_introduction(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_dut_summary(self, dut_code_dir) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_testbench_summary(self, bin_descr_dir) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_init_question(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_result_summary(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _load_coverage_difference_prompts_dict(self) -> Dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def _load_iter_question(self) -> str:
        raise NotImplementedError

    def generate_initial_prompt(self) -> str:
        # Initial Template: introduction + summaries + question
        initial_prompt = self.intro + '\n' + self.dut_summary + self.tb_summary + self.init_question
        return initial_prompt

    def generate_iterative_prompt(self, coverage_database: CoverageDatabase) -> str:
        # Iterative Template: result summary + difference + question
        coverage_difference = ""
        coverage_plan = get_coverage_plan(coverage_database)
        missed_bins = list(map(lambda p: p[0], filter(lambda p: p[1] == 0, coverage_plan.items())))
        if len(missed_bins) == 0:
            pass
        for bin_name in missed_bins:
            coverage_difference += self.coverage_difference_prompts_dict[bin_name]

        iterative_prompt = self.res_summary + '\n' + coverage_difference + '\n' + self.iter_question
        return iterative_prompt


class TemplatePromptGenerator4SD1(TemplatePromptGenerator):
    def _load_introduction(self) -> str:
        return ""

    def _load_dut_summary(self, dut_code_path) -> str:
        with open(dut_code_path, 'r') as f:
            dut_code = f.read()
        dut_summary = \
            f"I have a device under test (DUT). Here's the SystemVerilog code of the DUT:\n\n{dut_code}\n"
        return dut_summary

    def _load_testbench_summary(self, bin_descr_dir) -> str:
        with open(bin_descr_dir, 'r') as f:
            bins_description = f.read()
        tb_summary = \
            f"I also have a testbench that tests the DUT. Here's a description of the bins (i.e. test cases)" \
            f" that the testbench cares about:\n\n{bins_description}\n"
        return tb_summary

    def _load_init_question(self) -> str:
        init_question = \
            "Please generate segments of integers such that:\n" \
            "- Each segment has a length of 16.\n" \
            "- A segment follows a single-stride pattern with a stride width x if: " \
            "the differences between two adjacent integers are always x.\n" \
            "- A segment follows a double-stride pattern with a stride width pair (x, y) if: " \
            "the differences between two adjacent integers are alternating x and y, meanwhile" \
            " x and y are different.\n" \
            "- A segment has no stride pattern if it neither follows a single-stride pattern " \
            "nor a double-stride pattern.\n" \
            "- The maximum stride width is 15, and the minimum stride width is -16.\n" \
            "- For each bin described above, generate a segment."
        return init_question

    def _load_result_summary(self) -> str:
        result_summary = "The values you provided failed to satisfy all the bins. " \
                         "Here are the unreached bins:\n"
        return result_summary

    def _load_coverage_difference_prompts_dict(self) -> Dict[str, str]:
        single_bins_difference = {f'single_{i}': f"Single-stride pattern of stride width {i} is unreached.\n"
                                  for i in range(-16, 16)}
        double_bins_difference = {f'double_{i}_{j}': f"Double-stride pattern of stride width pair "
                                                     f"({i}, {j}) is unreached.\n"
                                  for i in range(-16, 16) for j in range(-16, 16) if i != j}
        misc_bins = ['single_stride_n_overflow',
                     'single_stride_p_overflow',
                     'double_stride_nn_overflow',
                     'double_stride_np_overflow',
                     'double_stride_pn_overflow',
                     'double_stride_pp_overflow',
                     'no_stride_to_double',
                     'no_stride_to_single',
                     'single_stride_to_double',
                     'double_stride_to_single']
        misc_bins_difference = {bin_name: f'{bin_name} is unreached.\n' for bin_name in misc_bins}

        coverage_difference_template = {**single_bins_difference, **double_bins_difference, **misc_bins_difference}
        return coverage_difference_template

    def _load_iter_question(self) -> str:
        iter_question = "Please regenerate these unreached segments according to " \
                        "the bins' descriptions"
        return iter_question
