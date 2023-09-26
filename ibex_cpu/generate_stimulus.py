#!/bin/env python3
import os
import sys
from datetime import datetime

import zmq
import pickle
from contextlib import closing

directory = os.path.dirname(os.path.abspath("__file__"))
sys.path.insert(0, os.path.dirname(directory))
# print(sys.path)

from agents.agent_LLM import *
from agents.agent_IC_dumb import *
from loggers.logger_csv import CSVLogger
from loggers.logger_txt import TXTLogger
from models.llm_gpt import ChatGPT
from ibex_cpu.shared_types import *
from stimuli_extractor import *
from stimuli_filter import *
from prompt_generators.prompt_generator_template_IC import *


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
        if not isinstance(state_coverage_obj[0], IbexStateInfo):
            raise RuntimeError("Bad format of coverage response element 0")
        if not isinstance(state_coverage_obj[1], CoverageDatabase):
            raise RuntimeError("Bad format of coverage response element 1")

        return state_coverage_obj

    def close(self):
        if self.socket:
            self.socket.close()


def main():
    print("Running main experiment on IC...\n")

    server_ip_port = input(
        "Please enter server's IP and port (e.g. 127.0.0.1:5050, 128.232.65.218:5555): "
    )

    prefix = f"./logs/"
    t = datetime.now()
    t = t.strftime("%Y%m%d_%H%M%S")

    # build components
    prompt_generator = TemplatePromptGenerator4IC2(
        bin_descr_path="../examples_IC/bins_description.txt",
        sampling_missed_bins_method="ICNEWEST",
    )

    stimulus_generator = ChatGPT(
        system_prompt=prompt_generator.generate_system_prompt(),
        best_iter_buffer_resetting="STABLE",
        compress_msg_algo="best 3",
        prioritise_harder_bins=False,
    )
    extractor = ICExtractor()
    stimulus_filter = ICFilter(0x0, 0xFFFFFFFF)

    # build loggers
    logger_txt = TXTLogger(f"{prefix}{t}.txt")
    logger_csv = CSVLogger(f"{prefix}{t}.csv")

    # create agent
    agent = LLMAgent(
        prompt_generator,
        stimulus_generator,
        extractor,
        stimulus_filter,
        [logger_txt, logger_csv],
        dialog_bound=700,
        rst_plan=rst_plan_SLOW,
    )
    print("Agent successfully built\n")

    # agent = DumbAgent4IC()

    stimulus = Stimulus(insn_mem_updates=[], finish=False)
    g_dut_state = GlobalDUTState()
    g_coverage = GlobalCoverageDatabase()

    with closing(StimulusSender(f"tcp://{server_ip_port}")) as stimulus_sender:
        while not agent.end_simulation(g_dut_state, g_coverage):
            stimulus.insn_mem_updates = agent.generate_next_value(
                g_dut_state, g_coverage
            )
            ibex_state, coverage = stimulus_sender.send_stimulus(stimulus)
            g_dut_state.set(ibex_state)
            g_coverage.set(coverage)

            if ibex_state.last_pc is not None:
                print(f"{ibex_state.last_pc:08x} {ibex_state.last_insn:08x}")

        stimulus.finish = True
        _, final_coverage = stimulus_sender.send_stimulus(stimulus)
        final_coverage.output()


if __name__ == "__main__":
    main()
