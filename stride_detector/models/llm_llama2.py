from llama import Llama

from stride_detector.models.llm_base import *


class Llama2(BaseLLM):
    def __init__(self,
                 system_prompt: str = "",
                 model_path='llama-2-7b-chat/',
                 tokenizer_path='tokenizer.model',
                 path_predix='../../llama2/',
                 # TODO: temperature tuning (high => random)
                 temperature=0.4,
                 top_p=0.9,
                 max_seq_len=10000,
                 max_batch_size=4,
                 max_gen_len=800):
        super().__init__(system_prompt)
        self.model_name = model_path.split('/')[0]

        self.generator = Llama.build(
            ckpt_dir=path_predix + model_path,
            tokenizer_path=path_predix + tokenizer_path,
            max_seq_len=max_seq_len,
            max_batch_size=max_batch_size,
        )
        self.temperature = temperature
        self.top_p = top_p
        self.max_gen_len = max_gen_len

        self.conversations = [[]]

        if self.system_prompt != "":
            self.conversations[-1].append({"role": "system", "content": self.system_prompt})

    def __str__(self):
        return self.model_name

    def __call__(self, prompt: str) -> str:
        # TODO: OR summarise previous dialogs?
        self._compress_conversation()
        self.conversations[-1].append({"role": "user", "content": prompt})

        results = self.generator.chat_completion(
            self.conversations,  # type: ignore
            max_gen_len=self.max_gen_len,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        response = results[-1]['generation']['content']

        # print the new dialog
        # print(f"{self.conversations[0][-1]['role'].capitalize()}: {self.conversations[0][-1]['content']}\n")
        # print(f"> {results[0]['generation']['role'].capitalize()}: {response}")

        self.conversations[-1].append({"role": "assistant", "content": response})

        return response

    def _compress_conversation(self):
        # TODO: relation between REMAIN_ITER_NUM and gibberish
        REMAIN_ITER_NUM = 3
        if len(self.conversations[-1]) < 4 + 2 * REMAIN_ITER_NUM:
            return
        if self.conversations[-1][0]['role'] == 'system':
            self.conversations[-1] = self.conversations[-1][:3] + self.conversations[-1][-2 * REMAIN_ITER_NUM:]
        else:
            self.conversations[-1] = self.conversations[-1][:2] + self.conversations[-1][-2 * REMAIN_ITER_NUM:]
        return

    def reset(self):
        self.conversations = [[]]
        if self.system_prompt != "":
            self.conversations[-1].append({"role": "system", "content": self.system_prompt})
