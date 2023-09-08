from llama import Llama

from models.llm_base import *


class Llama2(BaseLLM):
    def __init__(
        self,
        system_prompt: str = "",
        model_path="llama-2-7b-chat/",
        tokenizer_path="tokenizer.model",
        path_predix="../../llama2/",
        # TODO: temperature tuning (high => random)
        temperature=0.4,
        top_p=0.9,
        max_seq_len=10000,
        max_batch_size=4,
        max_gen_len=800,
        best_iter_buffer_resetting: str = "STABLE",
    ):
        super().__init__(system_prompt, best_iter_buffer_resetting)
        self.model_name = model_path.split("/")[0]

        self.generator = Llama.build(
            ckpt_dir=path_predix + model_path,
            tokenizer_path=path_predix + tokenizer_path,
            max_seq_len=max_seq_len,
            max_batch_size=max_batch_size,
        )
        self.temperature = temperature
        self.top_p = top_p
        self.max_gen_len = max_gen_len

        self.messages = [[]]
        if self.system_prompt != "":
            self.messages[-1].append({"role": "system", "content": self.system_prompt})

    def __str__(self):
        return self.model_name

    def __call__(self, prompt: str) -> str:
        self._compress_conversation()
        self.messages[-1].append({"role": "user", "content": prompt})

        results = self.generator.chat_completion(
            self.messages,  # type: ignore
            max_gen_len=self.max_gen_len,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        response = results[-1]["generation"]["content"]

        # print the new dialog
        # print(f"{self.messages[0][-1]['role'].capitalize()}: {self.messages[0][-1]['content']}\n")
        # print(f"> {results[0]['generation']['role'].capitalize()}: {response}")

        self.messages[-1].append({"role": "assistant", "content": response})
        self.total_msg_cnt += 1
        return response

    def _compress_conversation(self):
        # STABLE RST & CLEAR RST
        if self.best_iter_buffer_resetting in ["STABLE", "CLEAR"] and len(self.messages[-1]) < 4 + 2 * Llama2.REMAIN_ITER_NUM:
            return
        if self.messages[-1][0]["role"] == "system":
            init = self.messages[-1][:3]
        else:
            init = self.messages[-1][:2]
        # self.messages = init + self.messages[-2 * ChatGPT.REMAIN_ITER_NUM:]

        # Keep previous successful iter messages
        self.messages[-1] = init + self._select_successful()

        # print("Dialog compressed...")
        return

    def reset(self):
        self.messages = [[]]
        if self.system_prompt != "":
            self.messages[-1].append({"role": "system", "content": self.system_prompt})
        # CLEAR RST
        if self.best_iter_buffer_resetting == "CLEAR":
            self.best_messages.clear()
