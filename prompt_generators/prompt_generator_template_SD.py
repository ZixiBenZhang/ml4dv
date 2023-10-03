from prompt_generators.prompt_generator_template import *

BOUND = 523


class TemplatePromptGenerator4SD1(TemplatePromptGenerator):
    def __init__(
        self,
        dut_code_path: str = "../examples_SD/dut_code.txt",
        tb_code_path: str = "../examples_SD/tb_code.txt",
        bin_descr_path: str = "../examples_SD/bins_description.txt",
        code_summary_type: int = 0,  # 0: no code, 1: code, 2: summary
        sampling_missed_bins_method: Union[str, None] = None,
    ):
        super().__init__(
            dut_code_path,
            tb_code_path,
            bin_descr_path,
            code_summary_type,
            sampling_missed_bins_method,
        )

    def generate_system_prompt(self) -> str:
        return (
            "Please output a list of (positive or negative) integers only, "
            f"each integer between -{BOUND} and {BOUND}. \n"
            f"Output format: [a, b, c, ...]."
        )

    def _load_introduction(self) -> str:
        if self.code_summary_type == 1:
            return (
                "You will receive programs of a hardware device and a testbench, "
                "and a description of bins (i.e. test cases). "
                "Then, you are going to generate a list of integers to cover the test cases.\n"
            )
        elif self.code_summary_type == 0:
            return (
                "You will receive a description of bins (i.e. test cases) of a testbench for "
                "a hardware device under test (DUT). "
                "Then, you are going to generate a list of integers to cover these test cases.\n"
            )
        else:
            # TODO: intro for code summaries
            raise NotImplementedError

    def _load_code_summary(self, dut_code_path, tb_code_path) -> str:
        if self.code_summary_type == 0:
            return ""
        elif self.code_summary_type == 1:
            with open(dut_code_path, "r") as f:
                dut_code = f.read()
            with open(tb_code_path, "r") as f:
                tb_code = f.read()
            dut_summary = (
                f"I have a device under test (DUT). Here's the SystemVerilog code of the DUT:\n"
                f"------\n"
                f"DUT CODE\n"
                f"{dut_code}\n"
                f"------\n"
                f"I also have a testbench for the DUT. Here's the Python code of the testbench:\n"
                f"------\n"
                f"TESTBENCH CODE\n"
                f"{tb_code}\n"
                f"------\n"
            )
            return dut_summary
        else:
            # TODO: code summaries
            raise NotImplementedError

    def _load_bins_summary(self, bin_descr_dir, **kwargs) -> str:
        with open(bin_descr_dir, "r") as f:
            bins_description = f.read()
        tb_summary = (
            f"Now, we want to test the DUT with a list of integers as its input. "
            f"We want the input to cover the bins (i.e. test cases) that we care about. "
            f"Here's the description of the bins that we care about:\n"
            f"------\n"
            f"BINS DESCRIPTION\n"
            f"{bins_description}\n"
            f"------\n"
        )
        return tb_summary

    def _load_init_question(self) -> str:
        init_question = (
            "Following the bins description"
            + (", and refer to the programs" if self.code_summary_type != 0 else "")
            + ", generate a list that contains segments of integers, which covers "
            "the described bins as much as you can.\n"
        )
        return init_question

    def _load_result_summary(self, **kwargs) -> str:
        if kwargs["response_invalid"]:
            result_summary = (
                "Your response doesn't answer my query. \n"
                f"Please generate a list of integers between -{BOUND} and {BOUND}, "
                "with output format: [a, b, c, ...].\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''}the unreached bins:\n"
            )

        elif kwargs["no_new_hit"]:
            result_summary = (
                "The new values you just provided didn't cover any new bins. You need to try to cover as "
                "much of the described bins as you can.\n"
                "You will see the result coverage of your previous response(s), and then "
                "generate another list of integers to cover the unreached bins (i.e. test cases)\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''} the unreached bins:\n"
            )

        else:
            result_summary = (
                "The values you provided failed to cover all the bins.\n"
                "You will see the result coverage of your previous response(s), and then "
                "generate another list of integers to cover the unreached bins (i.e. test cases)\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''}the unreached bins:\n"
            )
        return result_summary

    def _load_coverage_difference_prompts_dict(self) -> Dict[str, str]:
        single_bins_difference = {
            f"single_{i}": f"- Single-stride pattern segment of stride width {i} is unreached.\n"
            for i in range(-16, 16)
        }
        double_bins_difference = {
            f"double_{i}_{j}": f"- Double-stride pattern segment of stride width pair "
            f"({i}, {j}) is unreached.\n"
            for i in range(-16, 16)
            for j in range(-16, 16)
            if i != j
        }
        misc_bins = [
            "single_stride_n_overflow",
            "single_stride_p_overflow",
            "double_stride_nn_overflow",
            "double_stride_np_overflow",
            "double_stride_pn_overflow",
            "double_stride_pp_overflow",
            "no_stride_to_double",
            "no_stride_to_single",
            "single_stride_to_double",
            "double_stride_to_single",
        ]
        misc_bins_difference = {
            bin_name: f"- {bin_name} is unreached.\n" for bin_name in misc_bins
        }

        coverage_difference_template = {
            **single_bins_difference,
            **double_bins_difference,
            **misc_bins_difference,
        }
        return coverage_difference_template

    def _load_iter_question(self, **kwargs) -> str:
        if kwargs["response_invalid"]:
            iter_question = (
                f"Please generate a list of integers between -{BOUND} and {BOUND}, "
                "with output format: [a, b, c, ...]."
            )
        else:
            iter_question = (
                "Please regenerate a segment of length 18 for each of these unreached bins "
                "according to the BINS DESCRIPTION."
            )
        return iter_question


# With negative examples
class TemplatePromptGenerator4SD2(TemplatePromptGenerator):
    def __init__(
        self,
        dut_code_path: str = "../examples_SD/dut_code.txt",
        tb_code_path: str = "../examples_SD/tb_code.txt",
        bin_descr_path: str = "../examples_SD/bins_description.txt",
        code_summary_type: int = 0,  # 0: no code, 1: code, 2: summary
        sampling_missed_bins_method: Union[str, None] = None,
    ):
        super().__init__(
            dut_code_path,
            tb_code_path,
            bin_descr_path,
            code_summary_type,
            sampling_missed_bins_method,
        )

    def generate_system_prompt(self) -> str:
        return (
            "Please output a list of (positive or negative) integers only, "
            f"each integer between -{BOUND} and {BOUND}. \n"
            f"Output format: [a, b, c, ...]."
        )

    def _load_introduction(self) -> str:
        if self.code_summary_type == 1:
            return (
                "You will receive programs of a hardware device and a testbench, "
                "and a description of bins (i.e. test cases). "
                "Then, you are going to generate a list of integers to cover the test cases.\n"
            )
        elif self.code_summary_type == 0:
            return (
                "You will receive a description of bins (i.e. test cases) of a testbench for "
                "a hardware device under test (DUT). "
                "Then, you are going to generate a list of integers to cover these test cases.\n"
            )
        else:
            # TODO: intro for code summaries
            raise NotImplementedError

    def _load_code_summary(self, dut_code_path, tb_code_path) -> str:
        if self.code_summary_type == 0:
            return ""
        elif self.code_summary_type == 1:
            with open(dut_code_path, "r") as f:
                dut_code = f.read()
            with open(tb_code_path, "r") as f:
                tb_code = f.read()
            dut_summary = (
                f"I have a device under test (DUT). Here's the SystemVerilog code of the DUT:\n"
                f"------\n"
                f"DUT CODE\n"
                f"{dut_code}\n"
                f"------\n"
                f"I also have a testbench for the DUT. Here's the Python code of the testbench:\n"
                f"------\n"
                f"TESTBENCH CODE\n"
                f"{tb_code}\n"
                f"------\n"
            )
            return dut_summary
        else:
            # TODO: code summaries
            raise NotImplementedError

    def _load_bins_summary(self, bin_descr_dir, **kwargs) -> str:
        with open(bin_descr_dir, "r") as f:
            bins_description = f.read()
        tb_summary = (
            f"Now, we want to test the DUT with a list of integers as its input. "
            f"We want the input to cover the bins (i.e. test cases) that we care about. "
            f"Here's the description of the bins that we care about:\n"
            f"------\n"
            f"BINS DESCRIPTION\n"
            f"{bins_description}\n"
            f"------\n"
        )
        return tb_summary

    def _load_init_question(self) -> str:
        init_question = (
            "Following the bins description"
            + (", and refer to the programs" if self.code_summary_type != 0 else "")
            + ", generate a list that contains segments of integers, which covers "
            "the described bins as much as you can.\n"
        )
        return init_question

    def _load_result_summary(self, **kwargs) -> str:
        if kwargs["response_invalid"]:
            result_summary = (
                "Your response doesn't answer my query. \n"
                f"Please generate a list of integers between -{BOUND} and {BOUND}, "
                "with output format: [a, b, c, ...].\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''}the unreached bins:\n"
            )

        elif kwargs["no_new_hit"]:
            result_summary = (
                "The new values you just provided didn't cover any new bins. You need to try to cover as "
                "much of the described bins as you can.\n"
                "You will see the result coverage of your previous response(s), and then "
                "generate another list of integers to cover the unreached bins (i.e. test cases)\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''} the unreached bins:\n"
            )

        else:
            result_summary = (
                "The values you provided failed to cover all the bins.\n"
                "You will see the result coverage of your previous response(s), and then "
                "generate another list of integers to cover the unreached bins (i.e. test cases)\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''}the unreached bins:\n"
            )
        return result_summary

    def _load_coverage_difference_prompts_dict(self) -> Dict[str, str]:
        single_bins_difference = {
            f"single_{i}": f"- Single-stride pattern segment of stride width {i} is unreached.\n"
            for i in range(-16, 16)
        }
        ### Negative examples
        double_bins_difference = {
            f"double_{i}_{j}": f"- Double-stride pattern segment of stride width pair "
            f"({i}, {j}) is unreached. This can be hit with a segment of "
            f"double-stride pattern with stride width pair ({i}, {j}). "
            f"DO NOT generate a segment of [{i}, {j}, {i}, {j}, ...] "
            f"because it can't cover this bin.\n"
            for i in range(-16, 16)
            for j in range(-16, 16)
            if i != j
        }
        misc_bins = [
            "single_stride_n_overflow",
            "single_stride_p_overflow",
            "double_stride_nn_overflow",
            "double_stride_np_overflow",
            "double_stride_pn_overflow",
            "double_stride_pp_overflow",
            "no_stride_to_double",
            "no_stride_to_single",
            "single_stride_to_double",
            "double_stride_to_single",
        ]
        misc_bins_difference = {
            bin_name: f"- {bin_name} is unreached.\n" for bin_name in misc_bins
        }

        coverage_difference_template = {
            **single_bins_difference,
            **double_bins_difference,
            **misc_bins_difference,
        }
        return coverage_difference_template

    def _load_iter_question(self, **kwargs) -> str:
        if kwargs["response_invalid"]:
            iter_question = (
                f"Please generate a list of integers between -{BOUND} and {BOUND}, "
                "with output format: [a, b, c, ...]."
            )
        else:
            iter_question = (
                "Please regenerate a segment of length 18 for each of these unreached bins "
                "according to the BINS DESCRIPTION."
            )
        return iter_question


# Analogy template prompting, see ./examples_SD_analogue/bins_description.txt
class TemplatePromptGenerator4SDAnalog(TemplatePromptGenerator):
    def __init__(
        self,
        dut_code_path: str = "../examples_SD_analogue/dut_code.txt",
        tb_code_path: str = "../examples_SD_analogue/tb_code.txt",
        bin_descr_path: str = "../examples_SD_analogue/bins_description.txt",
        code_summary_type: int = 0,  # 0: no code, 1: code, 2: summary
        sampling_missed_bins_method: Union[str, None] = None,
    ):
        super().__init__(
            dut_code_path,
            tb_code_path,
            bin_descr_path,
            code_summary_type,
            sampling_missed_bins_method,
        )

    def generate_system_prompt(self) -> str:
        return "Please output a list of (positive or negative) integers only."

    def generate_initial_prompt(self) -> str:
        # Initial Template: introduction + summaries + question
        initial_prompt = (
            self.intro
            + "\n\n"
            + self._load_bins_summary(self.bin_descr_path)
            + "\n\n"
            + self.init_question
        )
        return initial_prompt

    def _load_introduction(self) -> str:
        return (
            "Imagine a lock that can be unlocked with a particular sequence of numbers.  "
            "Your goal is to unlock as many locks as possible.  The numbers are integers and "
            "there are 16 in each sequence. "
        )

    def _load_code_summary(self, dut_code_path, tb_code_path) -> str:
        return ""

    def _load_bins_summary(self, bin_descr_dir, **kwargs) -> str:
        tb_summary = (
            f"Here are some definitions:\n"
            f"- A sequence follows a single-stride pattern with a stride width x if: "
            f"the differences between two adjacent integers are always x.\n"
            f"- A sequence follows a double-stride pattern with a stride width pair (x, y) if: "
            f"the differences between two adjacent integers are alternating x and y, "
            f"meanwhile x and y are different.\n"
            f"- A sequence has no stride pattern if it neither follows a single-stride pattern "
            f"nor a double-stride pattern.\n"
            f"- The maximum stride width is 15, and the minimum stride width is -16.\n\n"
            f"The locks can be unlocked with sequences that follow a single or double-stride pattern."
        )
        return tb_summary

    def _load_init_question(self) -> str:
        init_question = (
            "Only output the sequences of numbers and nothing else. "
            "Generate 10 example sequences that would unlock the locks.\n"
        )
        return init_question

    def generate_iterative_prompt(
        self, coverage_database: GlobalCoverageDatabase, **kwargs
    ) -> str:
        # Iterative Template: result summary + difference + question
        cur_coverage = coverage_database.get_coverage_rate()
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
        ) + "------\n" "LOCKS\n" + coverage_difference + "------\n" + self._load_iter_question(
            **kwargs
        )

        self.prev_coverage = cur_coverage
        return iterative_prompt

    def _load_result_summary(self, **kwargs) -> str:
        if kwargs["response_invalid"]:
            result_summary = (
                "Your response doesn't answer my query. "
                "Please only output the sequences of numbers and nothing else. \n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''}the locked locks:\n"
            )

        elif kwargs["no_new_hit"]:
            result_summary = (
                "Thank you, but your sequence of numbers failed to open any lock. \n"
                f"You will see {'several' if self.sampling_missed_bins else ''} locks that are still locked, "
                f"then try again to generate another sequence of numbers to unlock these locks\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''} the locked locks:\n"
            )

        else:
            result_summary = (
                "Thank you. Your sequence successfully opened some of the locks. \n"
                f"Now, you will see {'several' if self.sampling_missed_bins else ''} locks that are still locked, "
                f"then try again to generate a new sequence of numbers to unlock these locks\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''}the locked locks:\n"
            )
        return result_summary

    def _load_coverage_difference_prompts_dict(self) -> Dict[str, str]:
        single_bins_difference = {
            f"single_{i}": f"- Lock for single-stride pattern sequence of stride width {i} "
            f"is still locked. It can be unlocked by a sequence with "
            f"single-stride pattern with stride width of {i}\n"
            for i in range(-16, 16)
        }
        double_bins_difference = {
            f"double_{i}_{j}": f"- Lock for double-stride pattern sequence of stride width "
            f"pair ({i}, {j}) is still locked. It can be unlocked by a "
            f"sequence with double-stride pattern with stride width pair "
            f"of ({i}, {j})\n"
            for i in range(-16, 16)
            for j in range(-16, 16)
            if i != j
        }
        misc_bins_difference = {
            "single_stride_n_overflow": "- Special lock 'single_stride_n_overflow' is still locked. "
            "It can be unlocked by a sequence with single-stride pattern "
            "but with stride width lower than -16.\n",
            "single_stride_p_overflow": "- Special lock 'single_stride_p_overflow' is still locked. "
            "It can be unlocked by a sequence with single-stride pattern "
            "but with stride width higher than 15.\n",
            "double_stride_nn_overflow": "- Special lock 'double_stride_nn_overflow' is still locked. "
            "It can be unlocked by a sequence with double-stride pattern with "
            "stride width pair (x, y) but with both x and y lower than -16.\n",
            "double_stride_np_overflow": "- Special lock 'double_stride_np_overflow' is still locked. "
            "It can be unlocked by a sequence with double-stride pattern with "
            "stride width pair (x, y) but with x lower than -16 "
            "and y higher than 15.\n",
            "double_stride_pn_overflow": "- Special lock 'double_stride_pn_overflow' is still locked. "
            "It can be unlocked by a sequence with double-stride pattern with "
            "stride width pair (x, y) but with x higher than 15 "
            "and y lower than -16.\n",
            "double_stride_pp_overflow": "- Special lock 'double_stride_pp_overflow' is still locked. "
            "It can be unlocked by a sequence with double-stride pattern with "
            "stride width pair (x, y) but with both x and y higher than 15.\n",
            "no_stride_to_double": "- Special lock 'no_stride_to_double' is still locked. "
            "It can be unlocked by a sequence with no stride pattern followed by another "
            "sequence with double-stride pattern.\n",
            "no_stride_to_single": "- Special lock 'no_stride_to_single' is still locked. "
            "It can be unlocked by a sequence with no stride pattern followed by another "
            "sequence with single-stride pattern.\n",
            "single_stride_to_double": "- Special lock 'single_stride_to_double' is still locked. "
            "It can be unlocked by a sequence with single-stride pattern "
            "followed by another sequence with double-stride pattern.\n",
            "double_stride_to_single": "- Special lock 'single_stride_to_double' is still locked. "
            "It can be unlocked by a sequence with double-stride pattern "
            "followed by another sequence with single-stride pattern.\n",
        }

        coverage_difference_template = {
            **single_bins_difference,
            **double_bins_difference,
            **misc_bins_difference,
        }
        return coverage_difference_template

    def _load_iter_question(self, **kwargs) -> str:
        iter_question = (
            "Please only output the sequences of numbers and nothing else. "
            "Try again to generate sequences that would unlock the above locks.\n"
        )
        return iter_question
