from stride_detector.models.llm_base import *
import os
import openai
import tiktoken


class ChatGPT(BaseLLM):
    def __init__(self,
                 system_prompt: str = "",
                 model_name='gpt-3.5-turbo',
                 temperature=0.4,
                 top_p=1,
                 max_gen_tokens=800):
        super().__init__(system_prompt)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        assert openai_api_key is not None, "OpenAI API key not found."
        openai.api_key = openai_api_key
        self.model_name = model_name
        self.long_context_model_name = model_name + '-16k'  # not in use
        self.model_max_context = 4096 if 'gpt-3.5-turbo' in model_name else 8192 if 'gpt-4' in model_name else None
        self.temperature = temperature
        self.top_p = top_p
        self.max_gen_tokens = max_gen_tokens

        self.messages = []
        if self.system_prompt != "":
            self.messages.append({"role": "system", "content": self.system_prompt})

    def __str__(self):
        return self.model_name

    def __call__(self, prompt: str) -> str:
        self._compress_conversation()
        self.messages.append({"role": "user", "content": prompt})
        token_cnt = self._check_token_num()
        if self.model_max_context is None or token_cnt <= self.model_max_context:
            model = self.model_name
        else:
            model = self.long_context_model_name

        result = openai.ChatCompletion.create(
            model=model,
            messages=self.messages,
            temperature=self.temperature,
            top_p=self.top_p,
            max_tokens=self.max_gen_tokens,
            n=1,
        )
        response_choices: List[Dict[str, str]] = [choice['message'] for choice in result['choices']]

        self.messages.append(response_choices[0])
        return response_choices[0]['content']

    def _compress_conversation(self):
        REMAIN_ITER_NUM = 3
        if len(self.messages) < 4 + 2 * REMAIN_ITER_NUM:
            return
        if self.messages[-1]['role'] == 'system':
            init = self.messages[:3]
        else:
            init = self.messages[:2]
        self.messages = init + self.messages[-2 * REMAIN_ITER_NUM:]

        # TODO: compress by summarization using Ada?
        return

    def _check_token_num(self) -> int:
        return num_tokens_from_messages(self.messages, self.model_name)

    def reset(self):
        self.messages.clear()
        if self.system_prompt != "":
            self.messages.append({"role": "system", "content": self.system_prompt})


def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613") -> int:
    """Return the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        # print("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        # print("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}. 
            See https://github.com/openai/openai-python/blob/main/chatml.md for information on 
            how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
