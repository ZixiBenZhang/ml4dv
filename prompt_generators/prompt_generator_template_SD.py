from prompt_generators.prompt_generator_template import *


class TemplatePromptGenerator4SD1(TemplatePromptGenerator):
    def __init__(self,
                 dut_code_path: str = '../examples_SD/dut_code.txt',
                 tb_code_path: str = '../examples_SD/tb_code.txt',
                 bin_descr_path: str = '../examples_SD/bins_description.txt',
                 code_summary_type: int = 0,  # 0: no code, 1: code, 2: summary
                 sampling_missed_bins: bool = True,
                 ):
        super().__init__(dut_code_path, tb_code_path, bin_descr_path, code_summary_type, sampling_missed_bins)

    def _load_introduction(self) -> str:
        if self.code_summary_type == 1:
            return "You will receive programs of a hardware device and a testbench, " \
                   "and a description of bins (i.e. test cases). " \
                   "Then, you are going to generate a list of integers to cover the test cases.\n"
        elif self.code_summary_type == 0:
            return "You will receive a description of bins (i.e. test cases) of a testbench for " \
                   "a hardware device under test (DUT). " \
                   "Then, you are going to generate a list of integers to cover these test cases.\n"
        else:
            # TODO: intro for code summaries
            raise NotImplementedError

    def _load_code_summary(self, dut_code_path, tb_code_path) -> str:
        if self.code_summary_type == 0:
            return ""
        elif self.code_summary_type == 1:
            with open(dut_code_path, 'r') as f:
                dut_code = f.read()
            with open(tb_code_path, 'r') as f:
                tb_code = f.read()
            dut_summary = \
                f"I have a device under test (DUT). Here's the SystemVerilog code of the DUT:\n" \
                f"------\n" \
                f"DUT CODE\n" \
                f"{dut_code}\n" \
                f"------\n" \
                f"I also have a testbench for the DUT. Here's the Python code of the testbench:\n" \
                f"------\n" \
                f"TESTBENCH CODE\n" \
                f"{tb_code}\n" \
                f"------\n"
            return dut_summary
        else:
            # TODO: code summaries
            raise NotImplementedError

    def _load_bins_summary(self, bin_descr_dir) -> str:
        with open(bin_descr_dir, 'r') as f:
            bins_description = f.read()
        tb_summary = \
            f"Now, we want to test the DUT with a list of integers as its input. " \
            f"We want the input to cover the bins (i.e. test cases) that we care about. " \
            f"Here's the description of the bins that we care about:\n" \
            f"------\n" \
            f"BINS DESCRIPTION\n" \
            f"{bins_description}\n" \
            f"------\n"
        return tb_summary

    def _load_init_question(self) -> str:
        init_question = \
            "Following the bins description" + \
            (", and refer to the programs" if self.code_summary_type != 0 else "") + \
            ", generate a list that contains segments of integers, which covers " \
            "the described bins as much as you can.\n"
        return init_question

    def _load_result_summary(self, **kwargs) -> str:
        if kwargs['response_invalid']:
            result_summary = \
                "Your response doesn't answer my query. \n" \
                f"Please generate a list of integers between -{BOUND} and {BOUND}, " \
                "with output format: [a, b, c, ...].\n" \
                f"Here are {'some of ' if self.sampling_missed_bins else ''}the unreached bins:\n"

        elif kwargs['no_new_hit']:
            result_summary = \
                "The new values you just provided didn't cover any new bins. You need to try to cover as " \
                "much of the described bins as you can.\n" \
                "You will see the result coverage of your previous response(s), and then " \
                "generate another list of integers to cover the unreached bins (i.e. test cases)\n" \
                f"Here are {'some of ' if self.sampling_missed_bins else ''} the unreached bins:\n"

        else:
            result_summary = \
                "The values you provided failed to cover all the bins.\n" \
                "You will see the result coverage of your previous response(s), and then " \
                "generate another list of integers to cover the unreached bins (i.e. test cases)\n" \
                f"Here are {'some of ' if self.sampling_missed_bins else ''}the unreached bins:\n"
        return result_summary

    def _load_coverage_difference_prompts_dict(self) -> Dict[str, str]:
        # TODO: improve difference prompts?
        single_bins_difference = {f'single_{i}': f"- Single-stride pattern segment of stride width {i} is unreached.\n"
                                  for i in range(-16, 16)}
        double_bins_difference = {f'double_{i}_{j}': f"- Double-stride pattern segment of stride width pair "
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
        misc_bins_difference = {bin_name: f'- {bin_name} is unreached.\n' for bin_name in misc_bins}

        coverage_difference_template = {**single_bins_difference, **double_bins_difference, **misc_bins_difference}
        return coverage_difference_template

    def _load_iter_question(self, **kwargs) -> str:
        if kwargs['response_invalid']:
            iter_question = f"Please generate a list of integers between -{BOUND} and {BOUND}, " \
                            "with output format: [a, b, c, ...]"
        else:
            iter_question = "Please regenerate a segment of length 18 for each of these unreached bins " \
                            "according to the BINS DESCRIPTION."
        return iter_question
