from llama import Llama

from stride_detector.models.llm_base import *


class Llama2(BaseLLM):
    def __init__(self,
                 model_path='llama-2-7b-chat/',
                 tokenizer_path='tokenizer.model',
                 path_predix='../../llama2/',
                 temperature=0.85,
                 top_p=0.9,
                 max_seq_len=15000,
                 max_batch_size=4,
                 max_gen_len=1024,
                 system_format_prompt=""):
        super().__init__()
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

        self.system_prompt = system_format_prompt
        if self.system_prompt != "":
            self.conversations[-1].append({"role": "system", "content": self.system_prompt})

    def __str__(self):
        return self.model_name

    def __call__(self, prompt: str) -> str:
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

    def reset(self):
        self.conversations = [[]]
        if self.system_prompt != "":
            self.conversations[-1].append({"role": "system", "content": self.system_prompt})
