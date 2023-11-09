#!/bin/env python3
# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import zmq
import pickle
from contextlib import closing

from shared_types import *

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
    current_stride = 1
    stimulus = Stimulus(value = 0, finish = False)

    with closing(StimulusSender("tcp://localhost:5555")) as stimulus_sender:
        while current_stride <= STRIDE_MAX:
            dut_state, coverage = stimulus_sender.send_stimulus(stimulus)

            if coverage.stride_1_seen[current_stride] > 16:
                current_stride += 1

            stimulus.value += current_stride

        stimulus.value = None
        stimulus.finish = True
        stimulus_sender.send_stimulus(stimulus)

if __name__ == "__main__":
    main()
