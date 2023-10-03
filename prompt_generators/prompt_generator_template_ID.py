from prompt_generators.prompt_generator_template import *


class TemplatePromptGenerator4ID1(TemplatePromptGenerator):
    def __init__(
        self,
        dut_code_path: str = "../examples_ID/dut_code.txt",
        tb_code_path: str = "../examples_ID/tb_code.txt",
        bin_descr_path: str = "../examples_ID/bins_description.txt",
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
            "Please output a list of hexadecimal integers only, "
            f"each integer between 0x0 and 0xffffffff. \n"
            f"Do not give any explanations. \n"
            f"Output format: [a, b, c, ...]."
            # f"Output format: \n"
            # f"bin_name_1: a, \n"
            # f"bin_name_2: b, \n"
            # f"bin_name_3: c, \n"
            # f"..."
        )

    def _load_introduction(self) -> str:
        if self.code_summary_type == 1:
            return (
                "You will receive programs of a RISC-V instruction decoder and a testbench for it, "
                "as well as a description of bins (i.e. test cases). "
                "Then, you are going to generate a list of 32-bit instructions (i.e. hex integers "
                "between 0x0 and 0xffffffff) to cover the test cases.\n"
            )
        elif self.code_summary_type == 0:
            return (
                "You will receive a description of bins (i.e. test cases) of a testbench for "
                "a hardware device under test (DUT), which is a RISC-V instruction decoder. "
                "Then, you are going to generate a list of 32-bit instructions (i.e. hex integers between "
                "0x0 and 0xffffffff) to cover these test cases.\n"
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
            f"Now, we want to test the instruction decoder with a list of 32-bit instructions as its input. "
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
            + ", generate a list of 32-bit instructions (i.e. hex integers between 0x0 and 0xffffffff) "
            "which covers the described bins as much as you can.\n"
        )
        return init_question

    def _load_result_summary(self, **kwargs) -> str:
        if kwargs["response_invalid"]:
            result_summary = (
                "Your response doesn't answer my query. \n"
                f"Please generate a list of 32-bit instructions (i.e. hex integers between 0x0 and 0xffffffff), "
                "with output format: [a, b, c, ...].\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''}the unreached bins:\n"
            )

        elif kwargs["no_new_hit"]:
            result_summary = (
                "The new values you just provided didn't cover any new bins. You need to try to cover as "
                "much of the described bins as you can.\n"
                "You will see the result coverage of your previous response(s), and then "
                "generate another list of 32-bit instructions to cover the unreached bins (i.e. test cases)\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''} the unreached bins:\n"
            )

        else:
            result_summary = (
                "The values you provided failed to cover all the bins.\n"
                "You will see the result coverage of your previous response(s), and then "
                "generate another list of 32-bit instructions to cover the unreached bins (i.e. test cases)\n"
                f"Here are {'some of ' if self.sampling_missed_bins else ''}the unreached bins:\n"
            )
        return result_summary

    def _load_coverage_difference_prompts_dict(self) -> Dict[str, str]:
        alu = ["ADD", "SUB", "AND", "OR", "XOR", "SLL", "SRL", "SRA", "SLT", "SLTU"]
        op_bins = (
            alu
            + list(map(lambda s: f"{s}I", alu))
            + ["LW", "LH", "LB", "SW", "SH", "SB"]
        )

        ports = {
            "read_A_reg_": "read_A",
            "read_B_reg_": "read_B",
            "write_reg_": "write",
        }
        reg_bins = {
            f"{port}{i}": port_name
            for i in range(32)
            for port, port_name in ports.items()
        }

        # may have invalid cross bin entries that will never be in missed bins
        cross_bins = {
            f"{op}_x_{reg}": (op, port_name)
            for reg, port_name in reg_bins.items()
            for op in op_bins
        }

        op_bins_difference = {
            op: f"- {op}: there's no instruction that performs the operation {op}.\n"
            for op in op_bins
        }
        reg_bins_difference = {
            port: f"- {port}: there's no instruction that uses the {port_name} port of "
            f"register {port[-1]}.\n"
            for port, port_name in reg_bins.items()
        }
        cross_bins_difference = {
            bin_name: f"- {bin_name}: there's no operation that performs the operation {op_name} "
            f"using the {port_name} port of register {bin_name[-1]}.\n"
            for bin_name, (op_name, port_name) in cross_bins.items()
        }

        coverage_difference_template = {
            **op_bins_difference,
            **reg_bins_difference,
            **cross_bins_difference,
        }
        return coverage_difference_template

    def _load_iter_question(self, **kwargs) -> str:
        if kwargs["response_invalid"]:
            iter_question = (
                f"Please generate a list of 32-bit instructions (i.e. hex integers between "
                f"0x0 and 0xffffffff) , with output format: [a, b, c, ...]."
            )
        else:
            iter_question = (
                "Please regenerate a 32-bit instruction for each of these unreached bins "
                "according to the BINS DESCRIPTION."
            )
        return iter_question


# Succinct task introduction: Init as FixedPrompt, Iter as TemplatePrompt
class TemplatePromptGenerator4ID2(TemplatePromptGenerator4ID1):
    def __init__(
        self,
        dut_code_path: str = "../examples_ID/dut_code.txt",
        tb_code_path: str = "../examples_ID/tb_code.txt",
        bin_descr_path: str = "../examples_ID/bins_description.txt",
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

    def generate_initial_prompt(self, **kwargs) -> str:
        with open(self.bin_descr_path, "r") as f:
            bins_description = f.read()
        prompt = (
            "Please generate a list of 32-bit instructions (i.e. hex integers between 0x0 and 0xffffffff)"
            " for a RISC-V processor that satisfies these described bins (i.e. test cases):\n"
            "------\n"
            "BINS DESCRIPTION\n"
            f"{bins_description}"
            "------\n"
            "Please generate a list of 32-bit instructions (i.e. hex integers between 0x0 and 0xffffffff)"
            " that satisfies the above conditions."
        )
        return prompt


# Ask for long response when warmed up
class TemplatePromptGenerator4ID3(TemplatePromptGenerator4ID2):
    def __init__(
        self,
        dut_code_path: str = "../examples_ID/dut_code.txt",
        tb_code_path: str = "../examples_ID/tb_code.txt",
        bin_descr_path: str = "../examples_ID/bins_description.txt",
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

    def _load_iter_question(self, **kwargs) -> str:
        if kwargs["response_invalid"]:
            iter_question = (
                f"Please generate a list of 32-bit instructions (i.e. hex integers between "
                f"0x0 and 0xffffffff) , with output format: [a, b, c, ...]."
            )
        elif kwargs["warmed_up"]:
            iter_question = (
                "Please regenerate a list of 100 32-bit instruction for these unreached bins "
                "according to the BINS DESCRIPTION."
            )
            print("### Loaded prompt for long response...")
        else:
            iter_question = (
                "Please regenerate a 32-bit instruction for each of these unreached bins "
                "according to the BINS DESCRIPTION."
            )
        return iter_question
