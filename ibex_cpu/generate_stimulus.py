#!/usr/bin/env python3
# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import zmq
from contextlib import closing

from shared_types import Stimulus, CoverageDatabase, IbexStateInfo


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
    stimulus = Stimulus(insn_mem_updates=[], finish=False)

    with closing(StimulusSender("tcp://localhost:5555")) as stimulus_sender:
        while True:
            ibex_state, coverage = stimulus_sender.send_stimulus(stimulus)

            if ibex_state.last_pc is not None:
                print(f'{ibex_state.last_pc:08x} {ibex_state.last_insn:08x}')

            if ibex_state.last_pc == 0x100080 + 0x18:
                break

        stimulus.finish = True
        _, final_coverage = stimulus_sender.send_stimulus(stimulus)
        final_coverage.output()


if __name__ == "__main__":
    main()
