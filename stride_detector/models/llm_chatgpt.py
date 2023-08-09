from math import inf

from stride_detector.models.llm_base import *
import os
import openai


class ChatGPT(BaseLLM):
    def __init__(self,
                 system_prompt: str = "",
                 model_name='gpt-3.5-turbo',
                 temperature=1,
                 top_p=1,
                 max_tokens=inf):
        super().__init__(system_prompt)
        openai.api_key = os.getenv("OPENAI_API_KEY")
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

        result = openai.ChatCompletion.create(
            model=self.model_name,
            messages=self.messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            n=1,
        )
        response_choices: List[Dict[str, str]] = [choice['message'] for choice in result['choices']]

        self.messages.append(response_choices[0])
        return response_choices[0]['content']

    def reset(self):
        self.messages.clear()
        if self.system_prompt != "":
            self.messages.append({"role": "system", "content": self.system_prompt})
