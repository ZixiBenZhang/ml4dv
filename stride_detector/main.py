import os
from pprint import pprint

import fire as fire
# from llama import Llama
import openai


def testLlama(ckpt_dir='llama-2-7b-chat/', max_seq_len=4096, max_gen_len=None):
    generator = Llama.build(
        ckpt_dir=ckpt_dir,
        tokenizer_path='tokenizer.model',
        max_seq_len=max_seq_len,
        max_batch_size=4,
    )

    # a list of dialogs, should be length 1
    conversations = [[]]

    prompt = input("\nvvv Please enter SYSTEM prompt vvv\n")
    if not prompt == '':
        conversations[-1].append({
            "role": "system",
            "content": prompt})

    while True:
        prompt = input("\nvvv Please enter your query vvv\n")
        if prompt == '--exit':
            print("exiting...")
            break
        # NOT WORKING
        # elif prompt == '--clear':
        #     print("clearing...")
        #     conversations[-1] = [{"role": "user", "content": "Hello"}]
        #     conversations.append([])
        #     continue

        conversations[-1].append({"role": "user", "content": prompt})

        # returns a list of responses for the dialogs, should be length 1
        results = generator.chat_completion(
            conversations,  # type: ignore
            max_gen_len=max_gen_len,
            temperature=0.6,
            top_p=0.9,
        )

        # print the new dialog
        # print(f"{conversations[-1][-1]['role'].capitalize()}: {conversations[-1][-1]['content']}\n")
        print(f"> {results[-1]['generation']['role'].capitalize()}: {results[-1]['generation']['content']}")

        conversations[-1].append({"role": "assistant", "content": results[-1]['generation']['content']})


def testGPT():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = "What's Bayesian optimization?"
    messages = [{"role": "user", "content": prompt}]

    result = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages,
        n=3,
    )
    response_choices = [choice['message'] for choice in result['choices']]

    print("Responses:")
    for i, msg in enumerate(response_choices):
        print(f"Choice {i}:\n{msg}\n")


if __name__ == '__main__':
    fire.Fire(testGPT())
