from agents_for_dv import *
from stimuli_extractor import *

# >>>>> Unused <<<<<

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
