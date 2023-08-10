#!/bin/env python3

import zmq
import pickle
from contextlib import closing
import sys
import os

directory = os.path.dirname(os.path.abspath("__file__"))
sys.path.insert(0, os.path.dirname(directory))
# print(sys.path)

from shared_types import *
from agents.LLM_agent import *
from prompt_generators.prompt_generator_fixed import *
from prompt_generators.prompt_generator_template import *
from models.llm_llama2 import *
from models.llm_chatgpt import *


class StimulusSender:
    def __init__(self, zmq_addr):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(zmq_addr)

    def send_stimulus(self, stimulus_obj):
        self.socket.send_pyobj(stimulus_obj)
        state_coverage_obj = self.socket.recv_pyobj()

        if not isinstance(state_coverage_obj, tuple):
            raise RuntimeError("Bad format of coverage response")
        if not isinstance(state_coverage_obj[0], DUTState):
            raise RuntimeError("Bad format of coverage response element 0")
        if not isinstance(state_coverage_obj[1], CoverageDatabase):
            raise RuntimeError("Bad format of coverage response element 1")

        return state_coverage_obj

    def close(self):
        if self.socket:
            self.socket.close()


def main():
    prompt_generator = FixedPromptGenerator4SD1()
    stimulus_generator = Llama2(system_prompt=prompt_generator.generate_system_prompt())
    print('Llama2 successfully built')
    extractor = DumbExtractor()
    stimulus_filter = Filter4SD(-10000, 10000)

    t = datetime.now()
    t = t.strftime('%Y%m%d_%H%M%S')
    logger_txt = TXTLogger(f'./logs/{t}.txt')
    logger_csv = CSVLogger(f'./logs/{t}.csv')

    agent = LLMAgent(prompt_generator, stimulus_generator, extractor, stimulus_filter,
                     [logger_txt, logger_csv])
    print('Agent successfully built')

    stimulus = Stimulus(value=0, finish=False)
    dut_state = None
    coverage = None

    with closing(StimulusSender("tcp://128.232.65.218:5555")) as stimulus_sender:
        while not agent.end_simulation(dut_state, coverage):
            # print(f'Sending stimulus from dialog #{agent.dialog_index}')
            dut_state, coverage = stimulus_sender.send_stimulus(stimulus)
            # print('Generating next stimulus')
            stimulus.value = agent.generate_next_value(dut_state, coverage)

        stimulus.value = None
        stimulus.finish = True
        stimulus_sender.send_stimulus(stimulus)


if __name__ == "__main__":
    main()
