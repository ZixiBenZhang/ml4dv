#!/bin/env python3

from datetime import datetime
import zmq
import pickle
from contextlib import closing
import sys
import os

directory = os.path.dirname(os.path.abspath("__file__"))
sys.path.insert(0, os.path.dirname(directory))
# print(sys.path)

from stride_detector.shared_types import *
from global_shared_types import *
from agents.agent_LLM import LLMAgent
from prompt_generators.prompt_generator_fixed_SD import FixedPromptGenerator4SD1
from prompt_generators.prompt_generator_template_SD import TemplatePromptGenerator4SD1
from models.llm_llama2 import Llama2
from models.llm_chatgpt import ChatGPT
from stimuli_extractor import DumbExtractor
from stimuli_filter import Filter4SD
from loggers.logger_csv import CSVLogger
from loggers.logger_txt import TXTLogger


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
    # TODO: auto trials
    # build components
    prompt_generator = TemplatePromptGenerator4SD1()
    # if isinstance(prompt_generator, FixedPromptGenerator4SD1):
    #     prefix = '../logs_SD_fixed/'
    # elif isinstance(prompt_generator, TemplatePromptGenerator4SD1):
    #     prefix = '../logs_SD_template/'
    # else:
    #     raise TypeError(f"Prompt generator of type {type(prompt_generator)} is not supported")
    prefix = './logs/'

    # stimulus_generator = Llama2(system_prompt=prompt_generator.generate_system_prompt())
    # print('Llama2 successfully built')
    stimulus_generator = ChatGPT(system_prompt=prompt_generator.generate_system_prompt())
    extractor = DumbExtractor()
    stimulus_filter = Filter4SD(-10000, 10000)

    # build loggers
    t = datetime.now()
    t = t.strftime('%Y%m%d_%H%M%S')
    logger_txt = TXTLogger(f'{prefix}{t}.txt')
    logger_csv = CSVLogger(f'{prefix}{t}.csv')

    # create agent
    agent = LLMAgent(prompt_generator, stimulus_generator, extractor, stimulus_filter,
                     [logger_txt, logger_csv])
    print('Agent successfully built\n')

    # run test
    stimulus = Stimulus(value=0, finish=False)
    g_dut_state = GlobalDUTState()
    g_coverage = GlobalCoverageDatabase()

    server_ip_port = input("Please enter server's IP and port (e.g. 127.0.0.1:5050, 128.232.65.218:5555): ")

    with closing(StimulusSender(f"tcp://{server_ip_port}")) as stimulus_sender:
        while not agent.end_simulation(g_dut_state, g_coverage):
            stimulus.value = agent.generate_next_value(g_dut_state, g_coverage)
            dut_state, coverage = stimulus_sender.send_stimulus(stimulus)
            g_dut_state.set(dut_state)
            g_coverage.set(coverage)

        coverage_plan = {k: v for (k, v) in g_coverage.get_coverage_plan().items() if v > 0}
        print(f"Finished at dialog #{agent.dialog_index}, message #{agent.msg_index}, \n"
              f"with total {agent.total_msg_cnt} messages \n"
              f"Hits: {coverage_plan}, \n"
              f"Coverage rate: {g_coverage.get_coverage_rate()}\n")

        stimulus.value = None
        stimulus.finish = True
        stimulus_sender.send_stimulus(stimulus)


if __name__ == "__main__":
    main()
