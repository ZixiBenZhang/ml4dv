import stride_detector.shared_types
from prompt_generators.prompt_generator_base import *


class FixedPromptGenerator4ID1(BasePromptGenerator):
    def __init__(self):
        super().__init__()
        self.prev_coverage = (0, -1)

    def reset(self):
        self.prev_coverage = (0, -1)

    def generate_system_prompt(self) -> str:
        return (
            "Please output a list of hexadecimal integers only, "
            f"each integer between 0x0 and 0xffffffff. \n"
            f"Do not give any explanations. \n"
            f"Output format: [a, b, c, ...]."
        )

    def generate_initial_prompt(self) -> str:
        with open("../examples_ID/bins_description.txt", "r") as f:
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

    def generate_iterative_prompt(
        self, coverage_database: GlobalCoverageDatabase, **kwargs
    ) -> str:
        if kwargs["response_invalid"]:
            gibberish_prompt = (
                "Your response doesn't answer my query.\n"
                "Please output a list of hexadecimal integers only, "
                f"each integer between 0x0 and 0xffffffff, "
                f"with output format: [a, b, c, ...]."
            )
            return gibberish_prompt

        cur_coverage = coverage_database.get_coverage_rate()
        if cur_coverage == self.prev_coverage:
            prompt = (
                "The new values you just provided didn't cover any new bins.\n"
                "Please regenerate a list of 32-bit instructions to cover the bins you haven't covered."
            )
        else:
            prompt = (
                "The values you provided covered some but not all the bins.\n"
                "Please regenerate a list of 32-bit instructions to cover more bins."
            )
        self.prev_coverage = cur_coverage
        return prompt
