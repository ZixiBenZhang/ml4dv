from math import inf

from stride_detector.models.llm_base import *
import os
import openai


class ChatGPT(BaseLLM):
    def __init__(self,
                 system_prompt: str = "",
                 model_name='gpt-3.5-turbo',
                 temperature=0.4,
                 top_p=1,
                 max_tokens=inf):
        super().__init__(system_prompt)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        assert openai_api_key is not None, "OpenAI API key not found."
        openai.api_key = openai_api_key
        self.model_name = model_name
        self.temperature = temperature
        self.top_p = top_p
        self.max_tokens = max_tokens

        self.messages = []
        if self.system_prompt != "":
            self.messages.append({"role": "system", "content": self.system_prompt})

    def __str__(self):
        return self.model_name

    def __call__(self, prompt: str) -> str:
        self.messages.append({"role": "user", "content": prompt})

        # TODO: debug
        result = openai.ChatCompletion.create(
            model=self.model_name,
            messages=self.messages,
            temperature=self.temperature,
            top_p=self.top_p,
            # max_tokens=self.max_tokens,
            n=1,
        )
        response_choices: List[Dict[str, str]] = [choice['message'] for choice in result['choices']]

        self.messages.append(response_choices[0])
        return response_choices[0]['content']

    # not in use
    def _compress_conversation(self):
        REMAIN_ITER_NUM = 5
        if len(self.messages) < 4 + 2 * REMAIN_ITER_NUM:
            return
        if self.messages[-1]['role'] == 'system':
            init = self.messages[:3]
        else:
            init = self.messages[:2]
        self.messages = init + self.messages[-2 * REMAIN_ITER_NUM:]
        return

    def reset(self):
        self.messages.clear()
        if self.system_prompt != "":
            self.messages.append({"role": "system", "content": self.system_prompt})
