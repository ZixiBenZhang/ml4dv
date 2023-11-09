# Copyright Zixi Zhang
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from llama import Llama

from models.llm_base import *
from models.llm_gpt import num_tokens_from_messages


class Llama2(BaseLLM):
    def __init__(
        self,
        system_prompt: str = "",
        model_path="llama-2-7b-chat/",
        tokenizer_path="tokenizer.model",
        path_predix="../../llama2/",
        temperature=0.4,
        top_p=0.9,
        max_seq_len=10000,
        max_batch_size=4,
        max_gen_len=800,
        best_iter_buffer_resetting: str = "STABLE",
        compress_msg_algo: str = "best 3",
        prioritise_harder_bins: bool = True,
    ):
        super().__init__(
            system_prompt, best_iter_buffer_resetting, prioritise_harder_bins
        )
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
        self.recent_msgs = []
        if self.system_prompt != "":
            self.messages[-1].append({"role": "system", "content": self.system_prompt})

        self.compress_msg_algo: Callable[
            [], List[Dict[str, str]]
        ] = self.__resolve_msg_compress_algo(compress_msg_algo)

    def __resolve_msg_compress_algo(self, compress_msg_algo) -> Callable:
        if compress_msg_algo == "best 3":
            return self.__best_3
        elif compress_msg_algo == "best 2 recent 1":
            return self.__best_2_recent_1
        elif compress_msg_algo == "recent 3":
            return self.__recent_3
        else:
            raise TypeError(
                f"Invalid conversation compression algorithm {compress_msg_algo}."
            )

    def __str__(self):
        return self.model_name

    def __call__(self, prompt: str) -> Tuple[str, Tuple[int, int, int]]:
        self._compress_conversation()
        self.messages[-1].append({"role": "user", "content": prompt})
        self.recent_msgs.append({"role": "user", "content": prompt})

        results = self.generator.chat_completion(
            self.messages,  # type: ignore
            max_gen_len=self.max_gen_len,
            temperature=self.temperature,
            top_p=self.top_p,
        )
        response = results[-1]["generation"]["content"]

        self.messages[-1].append({"role": "assistant", "content": response})
        self.recent_msgs.append({"role": "assistant", "content": response})
        self.total_msg_cnt += 1
        input_token = num_tokens_from_messages(self.messages[-1][:-1])
        output_token = num_tokens_from_messages(self.messages[-1][-1:])
        total_token = input_token + output_token

        return response, (
            input_token,
            output_token,
            total_token,
        )

    def _compress_conversation(self):
        # STABLE RST & CLEAR RST
        if (
            self.best_iter_buffer_resetting in ["STABLE", "CLEAR"]
            and len(self.messages[-1]) < 4 + 2 * Llama2.REMAIN_ITER_NUM
        ):
            return
        if self.messages[-1][0]["role"] == "system":
            init = self.messages[-1][:3]
        else:
            init = self.messages[-1][:2]

        # Keep recent / previous successful iter messages
        self.messages[-1] = init + self.compress_msg_algo()
        # print("Dialog compressed...")
        return

    def __best_3(self) -> List[Dict[str, str]]:
        return self._select_successful(n_best=3)

    def __best_2_recent_1(self) -> List[Dict[str, str]]:
        best = self._select_successful(n_best=2)
        recent = self.recent_msgs[-2:]
        return best + recent

    def __recent_3(self) -> List[Dict[str, str]]:
        return self.messages[-1][-2 * 3 :]

    def reset(self):
        self.messages = [[]]
        if self.system_prompt != "":
            self.messages[-1].append({"role": "system", "content": self.system_prompt})
        # CLEAR RST
        if self.best_iter_buffer_resetting == "CLEAR":
            self.best_messages.clear()
