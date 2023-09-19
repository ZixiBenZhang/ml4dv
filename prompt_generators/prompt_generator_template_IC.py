from prompt_generators.prompt_generator_template import *


class TemplatePromptGenerator4IC1(TemplatePromptGenerator):
    def __init__(
        self,
        dut_code_path: str = "../examples_IC/dut_code.txt",
        tb_code_path: str = "../examples_IC/tb_code.txt",
        bin_descr_path: str = "../examples_IC/bins_description.txt",
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
        # TODO: refine SYSTEM prompt & output format (output updates OR whole instr memo?)
        return (
            f"Please output a list of pairs of hexadecimal integers only, "
            f"each integer between 0x0 and 0xffffffff. \n"
            f"Do not give any explanations. \n"
            f"Output format: [(a, i), (b, j), (c, k), ...]."
        )

    def _load_introduction(self) -> str:
        if self.code_summary_type == 1:
            raise NotImplementedError
            # return (
            #     "You will receive programs of a RISC-V instruction decoder and a testbench for it, "
            #     "as well as a description of bins (i.e. test cases). "
            #     "Then, you are going to generate a list of 32-bit instructions (i.e. hex integers "
            #     "between 0x0 and 0xffffffff) to cover the test cases.\n"
            # )
        elif self.code_summary_type == 0:
            # TODO: Template2: condense task introduction
            return (
                "You will receive a description of bins (i.e. test cases) of a testbench for "
                "a hardware device under test (DUT), which is a RISC-V CPU. "
                "Then, you are going to generate a list of pairs of 32-bit integers between "
                "0x0 and 0xffffffff to update the instruction memory in order to cover these test cases, "
                "where the first integer of the pair represents an address of the instruction memory, "
                "and the second integer of the pair represents a RISC-V instruction.\n"
            )
        else:
            raise NotImplementedError

    def _load_code_summary(self, dut_code_path, tb_code_path) -> str:
        if self.code_summary_type == 0:
            return ""
        elif self.code_summary_type == 1:
            raise NotImplementedError
        else:
            raise NotImplementedError

    def _load_bins_summary(self, bin_descr_dir, **kwargs) -> str:
        with open(bin_descr_dir, "r") as f:
            bins_description = f.read()
        tb_summary = (
            # TODO: instr memo bounds; pass in current instr memo??
            f"We are working with a CPU capable of executing RISC-V instructions. "
            f"The CPU's instruction memory is defined within the address range of "
            f"{0x00100080}, and its program counter (PC) is currently "
            f"set to {kwargs['current_pc']}. \n"
            f"Our objective is to update the CPU's instruction memory with a sequence "
            f"of 32-bit addresses and corresponding 32-bit instructions. The goal is "
            f"to ensure that, when the CPU resumes executing instructions from the "
            f"current PC, it covers the bins (i.e. test cases) that are of interest to us. \n"
            f"Here's the description of the bins that are of interest to us:\n"
            f"------\n"
            f"BINS DESCRIPTION\n"
            f"{bins_description}\n"
            f"------\n"
        )
        return tb_summary

    def _load_init_question(self) -> str:
        init_question = (
            "Generate a list, which can be empty if necessary, of address-instruction "
            "pairs in 32-bit hexadecimal format to update the CPU's memory, ensuring "
            "it covers the specified bins upon resuming execution from the current PC. \n"
        )
        return init_question

    def _load_result_summary(self, **kwargs) -> str:
        if kwargs["response_invalid"]:
            result_summary = (
                "Your response doesn't answer my query. \n"
                "Please generate a list of address-instruction pairs in 32-bit hexadecimal "
                "format (i.e. hex integers between 0x0 and 0xffffffff), with output format: "
                "[(a, i), (b, j), (c, k), ...].\n"
            )
        else:
            result_summary = "Thanks for your response.\n"

        # TODO: pass in current instr memo??
        result_summary += (
            f"The CPU has successfully executed numerous instructions following your update, "
            f"and its program counter (PC) is presently set to 0x0010008c. \n"
            f"You will now observe the coverage achieved by the CPU based on your previous "
            f"responses, and proceed to generate another list, which can be empty if necessary, "
            f"of address-instruction pairs to further modify the CPU's memory, ensuring it "
            f"covers the previously unreached bins (i.e. test cases) upon resuming execution "
            f"from the current PC.\n"
            f"Here are {'some of ' if self.sampling_missed_bins else ''}the unreached bins:\n"
        )
        return result_summary

    def _load_coverage_difference_prompts_dict(self) -> Dict[str, str]:
        # TODO: difference prompts
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
                "Please generate a list, which can be empty if necessary, of "
                "address-instruction pairs in 32-bit hexadecimal format (i.e. "
                "hex integers between 0x0 and 0xffffffff), with output format: "
                "[(a, i), (b, j), (c, k), ...].\n"
            )
        else:
            iter_question = (
                "Please generate a list, which can be empty if necessary, of address-instruction "
                "pairs in 32-bit hexadecimal format to further update the CPU's memory, "
                "ensuring it covers the specified unreached bins (i.e. test cases) upon resuming "
                "execution from the current PC.\n"
            )
        return iter_question


# Init as FixedPrompt, Iter as TemplatePrompt
# class TemplatePromptGenerator4ID2(TemplatePromptGenerator4ID1):
#     def __init__(
#         self,
#         dut_code_path: str = "../examples_ID/dut_code.txt",
#         tb_code_path: str = "../examples_ID/tb_code.txt",
#         bin_descr_path: str = "../examples_ID/bins_description.txt",
#         code_summary_type: int = 0,  # 0: no code, 1: code, 2: summary
#         sampling_missed_bins_method: Union[str, None] = None,
#     ):
#         super().__init__(
#             dut_code_path,
#             tb_code_path,
#             bin_descr_path,
#             code_summary_type,
#             sampling_missed_bins_method,
#         )
#         self.bin_descr_path = bin_descr_path
#
#     def generate_initial_prompt(self) -> str:
#         with open(self.bin_descr_path, "r") as f:
#             bins_description = f.read()
#         prompt = (
#             "Please generate a list of 32-bit instructions (i.e. hex integers between 0x0 and 0xffffffff)"
#             " for a RISC-V processor that satisfies these described bins (i.e. test cases):\n"
#             "------\n"
#             "BINS DESCRIPTION\n"
#             f"{bins_description}"
#             "------\n"
#             "Please generate a list of 32-bit instructions (i.e. hex integers between 0x0 and 0xffffffff)"
#             " that satisfies the above conditions."
#         )
#         return prompt
