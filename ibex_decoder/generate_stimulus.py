#!/bin/env python3
# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import zmq
import pickle
from contextlib import closing
from pprint import pprint

from shared_types import *

class StimulusSender:
    def __init__(self, zmq_addr):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(zmq_addr)

    def send_stimulus(self, stimulus_obj):
        self.socket.send_pyobj(stimulus_obj)
        coverage_obj = self.socket.recv_pyobj()

        if not isinstance(coverage_obj, CoverageDatabase):
            raise RuntimeError("Bad format of coverage response")

        return coverage_obj

    def close(self):
        if self.socket:
            self.socket.close()

# Test instructions
#  add x1, x2, x3
#  add x2, x3, x4
#  add x1, x3, x7
#
#  addi x18, x20, 1
#
#  xor x1, x2, x3
#  xor x1, x14, x17
#
#  lw x10, 16(x11)
#  lh x10, 16(x11)
#  lb x10, 16(x11)
#
#  sw x10, 16(x11)
#  sh x10, 16(x11)
#  sb x10, 16(x11)

test_insns = [
    0x003100b3,
    0x00418133,
    0x007180b3,
    0x001a0913,
    0x003140b3,
    0x011740b3,
    0x0105a503,
    0x01059503,
    0x01058503,
    0x00a5a823,
    0x00a59823,
    0x00a58823,
]

def main():
    with closing(StimulusSender("tcp://localhost:5555")) as stimulus_sender:
        for i in test_insns:
            coverage = stimulus_sender.send_stimulus(i)

        coverage = stimulus_sender.send_stimulus(None)

        coverage.output_coverage()

if __name__ == "__main__":
    main()
