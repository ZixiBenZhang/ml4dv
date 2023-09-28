from prompt_generators.prompt_generator_template import *
from ibex_cpu.instructions import Instr, Cov


class TemplatePromptGenerator4IC1(TemplatePromptGenerator):
    IMEM_LB = "0x00100080"
    IMEM_UB = "0x00100480"

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
        elif self.code_summary_type == 0:
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
            # TODO: pass in current instr memo??
            f"We are working with a CPU capable of executing RISC-V instructions. "
            f"The CPU's instruction memory is defined within the address range of "
            f"{self.IMEM_LB} to {self.IMEM_UB}, and its program counter (PC) is currently "
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
            f"Following the bins description, generate a list, which can be empty if "
            f"necessary, of address-instruction pairs $(a, i)$ in 32-bit hexadecimal format "
            f"to update the CPU's memory, ensuring it covers the specified bins upon resuming "
            f"execution from the current PC. Make sure the addresses $a$ are in the range of "
            f"{self.IMEM_LB} to {self.IMEM_UB}, and the instructions $i$ are valid RISC-V instruction codes.\n"
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
        elif kwargs["update_invalid"]:
            result_summary = (
                "Your list of updates was invalid, either because the addresses are out-of-bound"
                "or the instructions you provided are not valid R-type, S-type, or J-type RISC-V "
                "instructions. Try to amend it in your new response. \n"
                f"The CPU has executed numerous instructions following your last update. The last "
                f"instruction performed was {kwargs['last_instr']}, and the program counter (PC) is "
                f"presently set to {kwargs['current_pc']}. \n"
            )
        else:
            result_summary = (
                f"Thanks for your response.\n"
                f"The CPU has successfully executed numerous instructions following your update. "
                f"The last instruction performed was {kwargs['last_instr']}, and the program counter (PC) is "
                f"presently set to {kwargs['current_pc']}. \n"
            )

        # TODO: pass in current instr memo??
        result_summary += (
            f"You will now observe the bins haven't been achieved by the CPU, and proceed to "
            f"generate another list, which can be empty if necessary, "
            f"of address-instruction pairs to further modify the CPU's memory, ensuring it "
            f"covers the previously unreached bins (i.e. test cases) upon resuming execution "
            f"from the current PC.\n"
            f"Here are {'some of ' if self.sampling_missed_bins else ''}the unreached bins:\n"
        )
        return result_summary

    def _load_coverage_difference_prompts_dict(self) -> Dict[str, str]:
        basic_bins = {
            "seen": [],
            "zero_dst": [],
            "zero_src": [],
            "same_src": [],
            "br_backwards": [],
            "br_forwards": [],
        }
        for instr in Instr:
            for cov in instr.type().coverpoints():
                basic_bins[cov.value].append(instr.value)

        raw_bins = []
        for instr in Instr:
            for prev_instr, cov in instr.type().cross_coverpoints():
                raw_bins.append((prev_instr.value, instr.value, cov.value))

        basic_bins_difference = {}
        for op in basic_bins["seen"]:
            basic_bins_difference[
                f"{op}_seen"
            ] = f"- {op}_seen: the CPU hasn't performed the operation {op}.\n"
        for op in basic_bins["zero_dst"]:
            basic_bins_difference[f"{op}_zero_dst"] = (
                f"- {op}_zero_dst: the CPU hasn't executed an instruction "
                f"that performs the operation {op} with register zero as "
                f"the destination register.\n"
            )
        for op in basic_bins["zero_src"]:
            basic_bins_difference[f"{op}_zero_src"] = (
                f"- {op}_zero_src: the CPU hasn't executed an instruction "
                f"that performs the operation {op} with register zero as "
                f"one of the source registers.\n"
            )
        for op in basic_bins["same_src"]:
            basic_bins_difference[f"{op}_same_src"] = (
                f"- {op}_same_src: the CPU hasn't executed an instruction "
                f"that performs the operation {op} with same source registers.\n"
            )
        for op in basic_bins["br_backwards"]:
            basic_bins_difference[f"{op}_br_backwards"] = (
                f"- {op}_br_backwards: the CPU hasn't performed a {op} "
                f"operation that makes a backward jump.\n"
            )
        for op in basic_bins["br_forwards"]:
            basic_bins_difference[f"{op}_br_forwards"] = (
                f"- {op}_br_backwards: the CPU hasn't performed a {op} "
                f"operation that makes a forward jump.\n"
            )

        raw_bins_difference = {
            f"{prev_instr}->{instr}_{cov}": f"- {prev_instr}->{instr}_{cov}: the CPU hasn't perform a "
            f"{prev_instr} operation followed by a {instr} operation with "
            f"RaW hazard, in which the second operation has a source register "
            f"that is the same as the destination register of the first operation.\n"
            for prev_instr, instr, cov in raw_bins
        }

        coverage_difference_template = {
            **basic_bins_difference,
            **raw_bins_difference,
        }
        return coverage_difference_template

    def _load_iter_question(self, **kwargs) -> str:
        if kwargs["response_invalid"]:
            iter_question = (
                f"Please generate a list, which can be empty if necessary, of "
                f"address-instruction pairs in 32-bit hexadecimal format (i.e. "
                f"hex integers between 0x0 and 0xffffffff), with output format: "
                f"[(a, i), (b, j), (c, k), ...]. Make sure the addresses are in "
                f"the range of {self.IMEM_LB} to {self.IMEM_UB}, and the instructions "
                f"are valid RISC-V instruction codes.\n"
            )
        else:
            iter_question = (
                f"Please generate a list, which can be empty if necessary, of address-instruction "
                f"pairs in 32-bit hexadecimal format to further update the CPU's memory, "
                f"ensuring it covers the specified unreached bins (i.e. test cases) upon resuming "
                f"execution from the current PC. Make sure the addresses are in the range of "
                f"{self.IMEM_LB} to {self.IMEM_UB}, and the instructions are valid R-type, S-type, "
                f"or J-type instructions. We encourage you to make updates near the current PC ({kwargs['current_pc']}), "
                f"and update addresses into diverse variety of operations. \n"
            )
        return iter_question


# Succinct task introduction
class TemplatePromptGenerator4IC2(TemplatePromptGenerator4IC1):
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

    def generate_initial_prompt(self, **kwargs) -> str:
        with open(self.bin_descr_path, "r") as f:
            bins_description = f.read()
        prompt = (
            # TODO: pass in current instr memo??
            f"We are working with a CPU capable of executing RISC-V instructions. "
            f"The CPU's instruction memory is defined within the address range of "
            f"{self.IMEM_LB} to {self.IMEM_UB}, where 0x00100098 is currently the return instruction "
            f"of the process. The program counter (PC) is currently set to "
            f"{kwargs['current_pc']}. \n"
            f"Our objective is to update the CPU's instruction memory with a sequence "
            f"of 32-bit addresses and corresponding 32-bit instructions. The goal is "
            f"to ensure that, when the CPU resumes executing instructions from the "
            f"current PC, it covers the bins (i.e. test cases) that are of interest to us. \n"
            f"Here's the description of the bins that are of interest to us:\n"
            "------\n"
            "BINS DESCRIPTION\n"
            f"{bins_description}"
            "------\n"
            f"Following the bins description, generate a list, which can be empty if "
            f"necessary, of address-instruction pairs $(a, i)$ in 32-bit hexadecimal format "
            f"to update the CPU's memory, ensuring it covers the specified bins upon resuming "
            f"execution from the current PC. Make sure the addresses $a$ are in the range of "
            f"{self.IMEM_LB} to {self.IMEM_UB}, and the instructions $i$ are VALID R-type, S-type, "
            f"or J-type instructions. We encourage you to make updates near the current PC ({kwargs['current_pc']}), "
            f"and update addresses into diverse variety of operations. \n"
        )
        return prompt
