from agents_for_dv import *
from stimuli_extractor import *


class DumbAgent4SD(BaseAgent):
    def __init__(self):
        super().__init__()
        self.current_stride = 1
        self.new_value = None
        self.NUM_STRIDES = 32
        self.STRIDE_MIN = -16
        self.STRIDE_MAX = 15

    def reset(self):
        self.new_value = None
        self.current_stride = 1

    def end_simulation(self, coverage_database: Union[None, CoverageDatabase]):
        return not self.current_stride <= self.STRIDE_MAX

    def generate_next_value(self, coverage_database: Union[None, CoverageDatabase]):
        if self.new_value is None:
            self.new_value = 1
            return self.new_value

        if coverage_database.stride_1_seen[self.current_stride] > 16:
            self.current_stride += 1

        return self.new_value + self.current_stride


# class FSChatAgent(BaseAgent):
#     # Please launch the RESTful API server before making interactions
#     # python3 -m fastchat.serve.controller
#     # python3 -m fastchat.serve.model_worker --model-path lmsys/vicuna-7b-v1.3
#     # python3 -m fastchat.serve.openai_api_server --host localhost --port 8000
#
#     def __init__(self, model_path="lmsys/vicuna-7b-v1.3"):
#         super().__init__()
#         openai.api_key = "EMPTY"  # Not support yet
#         openai.api_base = "http://localhost:8000/v1"
#         self.model = model_path
#         self.prompt = None
#         self.conversation = []
#
#         # prompts for generating stimuli for unreached bins
#         self.initial_prompt = \
#             'Generate a stream of integers. Each integer is a 32-bit integer. Make sure the stream consists of ' \
#             'single-stride segments for strides between -3 and 3. Each segment has a length of 16. A single-stride ' \
#             'segment of stride x ensures every two adjacent integers have a difference equal to x. Please only ' \
#             'include the integer stream in your output. '
#         self.general_prompt = 'These are not complete. Please give me the rest of the segments.'
#         self.single_stride_bin_prompt = {}
#         self.double_stride_bin_prompt = {}
#         self.misc_bin_prompts = {
#             'single_stride_n_overflow': '',
#             'single_stride_p_overflow': '',
#             'double_stride_nn_overflow': '',
#             'double_stride_np_overflow': '',
#             'double_stride_pn_overflow': '',
#             'double_stride_pp_overflow': '',
#             'no_stride_to_double': '',
#             'no_stride_to_single': '',
#             'single_stride_to_double': '',
#             'double_stride_to_single': '',
#         }
#
#         self.prompt = self.initial_prompt
#
#     def reset(self):
#         self.prompt = self.initial_prompt
#         self.conversation.clear()
#
#     def end_simulation(self):
#         pass
#
#     def generate_next_value(self):
#         self.conversation.append({"role": "user", "content": self.prompt})
#
#         # create a chat completion
#         completion = openai.ChatCompletion.create(
#             model=self.model,
#             messages=self.conversation
#         )
#
#         # print the completion
#         res = completion.choices[0].message.content
#         print(res)
#         self.conversation.append({"role": "assistant", "content": res})
#
#         # parse res to extract stimuli (by specifying format in prompt?)
#
#         # choose next prompt based on res
#         self.prompt = self.general_prompt
#
#         # return the stimulus value
#         return 1


class LLMAgent4SD(LLMAgent):
    def _load_dut_code(self) -> str:
        with open("stride_detector.sv", 'r') as f:
            dut_code = f.read()
        return dut_code

    def _load_bins_description(self) -> str:
        bins_description = \
            "- stride_1_seen - One bin per possible stride width between the minimum and maximum stride " \
            "width, where the segment follows a single-stride pattern of the stride width.\n" \
            "- stride_2_seen - One bin per pair of possible stride widths between the minimum and maximum " \
            "stride width, where the segment follows a double-stride pattern of the stride width pair.\n" \
            "- misc_bins - Various bins grouped in a dictionary\n" \
            "    - single_stride_[n|p]_overflow - A segment where an incoming stream of values has a valid " \
            "single stride but that stride is below the minimum (n) or above the maximum (p) stride width.\n" \
            "    - double_stride_[n|p][n|p] - A segment where an incoming stream of values has a valid double " \
            "stride but those strides are below the minimum (n) or above the maximum (p) stride widths, " \
            "nn indicates both are below the minimum, where np indicates one is below the minimum and the " \
            "other above the maximum.\n" \
            "    - no_stride_to_[single|double] - A segment with no stride pattern followed by another " \
            "segment with a single/double stride pattern.\n" \
            "    - [single|double]_stride_[double|single] - A segment with single/double stride pattern " \
            "followed by another segment with a double/single stride pattern.\n"
        return bins_description

    def _generate_init_question(self) -> str:
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

    def _generate_coverage_difference_prompts(self) -> dict:
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

    def _generate_iter_question(self) -> str:
        iter_question = "Please regenerate these unreached segments according to " \
                        "the bins' descriptions"
        return iter_question

    @abstractmethod
    def _query_to_LLM(self, prompt) -> str:
        pass


class Llama2Agent4SD(LLMAgent4SD):
    def __init__(self,
                 model_path='llama-2-7b-chat/',
                 tokenizer_path='tokenizer.model',
                 temperature=0.6,
                 top_p=0.9,
                 max_seq_len=8192,
                 max_batch_size=4,
                 max_gen_len=None):
        # from llama import Llama
        super().__init__()

        self.generator = Llama.build(
            ckpt_dir=model_path,
            tokenizer_path=tokenizer_path,
            max_seq_len=max_seq_len,
            max_batch_size=max_batch_size,
        )
        self.temperature = temperature
        self.top_p = top_p
        self.max_gen_len = max_gen_len

        self.extractor = DumbExtractor()

        self.conversations = [[]]

        # TODO: initial SYSTEM prompt describing output format
        self.system_prompt = ""
        if not self.system_prompt == '':
            self.conversations[-1].append({"role": "system", "content": self.system_prompt})

    def reset(self):
        self.state = 'INIT'
        self.stimuli_buffer.clear()
        self.stimulus_cnt = 0
        self.conversations = [[]]

    def _query_to_LLM(self, prompt) -> str:
        self.conversations[0].append({"role": "user", "content": prompt})

        results = self.generator.chat_completion(
            self.conversations,  # type: ignore
            max_gen_len=self.max_gen_len,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        response = results[0]['generation']['content']

        # print the new dialog
        # print(f"{self.conversations[0][-1]['role'].capitalize()}: {self.conversations[0][-1]['content']}\n")
        # print(f"> {results[0]['generation']['role'].capitalize()}: {response}")

        self.conversations[0].append({"role": "assistant", "content": response})

        return response
