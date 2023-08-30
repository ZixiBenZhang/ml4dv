import stride_detector.shared_types
from prompt_generators.prompt_generator_base import *

BOUND = 523


class FixedPromptGenerator4SD1(BasePromptGenerator):
    def __init__(self):
        super().__init__()
        self.prev_coverage = (0, -1)

    def reset(self):
        self.prev_coverage = (0, -1)

    def generate_system_prompt(self) -> str:
        return (
            "Please output (positive or negative) a list of integers only, "
            f"each integer between -{BOUND} and {BOUND}. \n"
            f"Output format: [a, b, c, ...]."
        )

    def generate_initial_prompt(self) -> str:
        prompt = (
            "Please generate a list of integers that satisfies these conditions:\n"
            "------\n"
            "CONDITIONS\n"
            f"- The list contains segments (i.e. subsequences) of integers, each between -{BOUND} and {BOUND}.\n"
            "- Each segment is of length 16.\n"
            "- A segment follows a single-stride pattern with a stride width x if: the differences between "
            "two adjacent integers are always x.\n"
            "- A segment follows a double-stride pattern with a stride width pair (x, y) if: the differences "
            "between two adjacent integers are alternating x and y, meanwhile x and y are different.\n"
            "- A segment has no stride pattern if it neither follows a single-stride pattern nor a "
            "double-stride pattern.\n"
            "- The maximum stride width is 15, and the minimum stride width is -16.\n"
            "- For each bin described as the following, generate a segment:\n"
            "---\n"
            "BINS\n"
            "- stride_1_seen - One bin per possible stride width between the minimum and maximum stride width, "
            "where the segment follows a single-stride pattern of the stride width.\n"
            "- stride_2_seen - One bin per pair of possible stride widths between the minimum and maximum "
            "stride width, where the segment follows a double-stride pattern of the stride width pair.\n"
            "- misc_bins - Various bins grouped in a dictionary\n"
            "    - single_stride_[n|p]_overflow - A segment where an incoming stream of values has a valid single "
            "stride but that stride is below the minimum (n) or above the maximum (p) stride width.\n"
            "    - double_stride_[n|p][n|p] - A segment where an incoming stream of values has a valid double stride "
            "but those strides are below the minimum (n) or above the maximum (p) stride widths, nn indicates both "
            "are below the minimum, where np indicates one is below the minimum and the other above the maximum.\n"
            "---\n"
            "- Also, generate consecutive segments that satisfy the following bins:\n"
            "---\n"
            "BINS"
            "    - no_stride_to_[single|double] - A segment with no stride pattern followed by another segment with "
            "a single/double stride pattern.\n"
            "    - [single|double]_stride_[double|single] - A segment with single/double stride pattern followed by "
            "another segment with a double/single stride pattern.\n"
            "---\n"
            "------\n"
            f"Please generate a list of integers between -{BOUND} and {BOUND} that satisfies the above conditions.\n"
        )
        return prompt

    def generate_iterative_prompt(
        self, coverage_database: GlobalCoverageDatabase, **kwargs
    ) -> str:
        if kwargs["response_invalid"]:
            gibberish_prompt = (
                "Your response doesn't answer my query.\n"
                f"Please generate a list of integers, "
                f"each integer between -{BOUND} and {BOUND}, "
                "with output format: [a, b, c, ...]"
            )
            return gibberish_prompt

        cur_coverage = coverage_database.get_coverage_rate()
        if cur_coverage == self.prev_coverage:
            prompt = (
                "The new values you just provided didn't cover any new bins.\n"
                "Please regenerate a list of integers to cover the bins you haven't covered."
            )
        else:
            prompt = (
                "The values you provided covered some but not all the bins.\n"
                "Please regenerate a list of integers to cover more bins."
            )
        self.prev_coverage = cur_coverage
        return prompt
