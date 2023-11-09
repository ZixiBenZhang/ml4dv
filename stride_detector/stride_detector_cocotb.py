# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import functools
import zmq
import pickle
from contextlib import closing
from shared_types import *

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, ClockCycles, ReadWrite, ReadOnly, Event


NO_STRIDE = 0
SINGLE_STRIDE = 1
DOUBLE_STRIDE = 2

# Gathers the coverage, coverage bins are:
# * stride_1_seen - One bin per possible stride, counts when a single stride has
#   been detected
# * stride_2_seen - One bin per pair of possible strides, counts when a double
#   stride has been detected. Note that the bins where both strides are the same
#   will never be hit (as these are single stride patterns)
# * misc_bins - Various bins grouped in a dictionary
#  - single_stride_[n|p]_overflow - Counts when an incoming stream of values
#    has a valid single stride but that stride is below the minimimum (n) or
#    above the maximum (p) stride
#  - double_stride_[n|p][n|p] - Counts when an incoming stream of values
#    has a valid double stride but those strides ar below the minimimum (n) or
#    above the maximum (p) strides, nn indicates both a below the minimum, where
#    np indicataes one is below the minimum and the other above the maximum.
#  - no_stride_to_[single|double] - No repeating stride pattern has been
#    observed in values for at least 16 values followed by the observation of a
#    single/double stride pattern for at least 16 values
#  - [single|double]_stride_[double|single] - A single/double repeating stride
#    pattern has been observed followed by a double/single pattern

class CoverageMonitor:
    def __init__(self, dut):
        self.coverage_database = CoverageDatabase()

        self.coverage_database.stride_1_seen = [0] * NUM_STRIDES
        self.coverage_database.stride_2_seen = []

        for i in range(NUM_STRIDES):
            self.coverage_database.stride_2_seen.append([0] * NUM_STRIDES)

        self.signals = {
                'clk'   : dut.clk_i,
                'valid' : dut.valid_i,
                'value' : dut.value_i,
                'stride_1' : dut.stride_1_o,
                'stride_1_valid' : dut.stride_1_valid_o,
                'stride_2' : dut.stride_2_o,
                'stride_2_valid' : dut.stride_2_valid_o,
        }

        self.coverage_database.misc_bins = {
                'single_stride_n_overflow' : 0,
                'single_stride_p_overflow' : 0,
                'double_stride_nn_overflow' : 0,
                'double_stride_np_overflow' : 0,
                'double_stride_pn_overflow' : 0,
                'double_stride_pp_overflow' : 0,
                'no_stride_to_double' : 0,
                'no_stride_to_single' : 0,
                'single_stride_to_double' : 0,
                'double_stride_to_single' : 0,
        }

        self.stride_state = NO_STRIDE
        self.no_strides_count = 0

        self.last_values = []

        self.coverage_sampled_event = Event()

    def sample_coverage(self):
        if self.signals['valid'].value:
            self.last_values.append(int(self.signals['value'].value))

            if len(self.last_values) > 16:
                self.last_values = self.last_values[-16:]

        if self.signals['stride_1_valid'].value:
            if self.signals['stride_2_valid'].value:
                self.coverage_database.stride_2_seen[self.signals['stride_1'].value][self.signals['stride_2'].value] += 1
            else:
                self.coverage_database.stride_1_seen[self.signals['stride_1'].value] += 1

        self.check_latest_strides()
        self.coverage_sampled_event.set()

    def sample_single_stride_coverage(self, single_stride):
        no_stride = True

        if single_stride < STRIDE_MIN:
            self.coverage_database.misc_bins['single_stride_n_overflow'] += 1
        elif single_stride > STRIDE_MAX:
            self.coverage_database.misc_bins['single_stride_p_overflow'] += 1
        else:
            no_stride = False

            if self.stride_state == NO_STRIDE:
                self.coverage_database.misc_bins['no_stride_to_single'] += 1
            elif self.stride_state == DOUBLE_STRIDE:
                self.coverage_database.misc_bins['double_stride_to_single'] += 1

            self.stride_state = SINGLE_STRIDE
            self.no_strides_count = 0

        if no_stride:
            self.no_strides_count += 1

    def sample_double_stride_coverage(self, first_stride, second_stride):
        no_stride = True

        if first_stride < STRIDE_MIN and second_stride < STRIDE_MIN:
            self.coverage_database.misc_bins['double_stride_nn_overflow'] += 1
        if first_stride < STRIDE_MIN and second_stride > STRIDE_MAX:
            self.coverage_database.misc_bins['double_stride_np_overflow'] += 1
        if first_stride > STRIDE_MAX and second_stride < STRIDE_MIN:
            self.coverage_database.misc_bins['double_stride_pn_overflow'] += 1
        if first_stride > STRIDE_MAX and second_stride > STRIDE_MAX:
            self.coverage_database.misc_bins['double_stride_pp_overflow'] += 1
        else:
            no_stride = False
            if self.stride_state == NO_STRIDE:
                self.coverage_database.misc_bins['no_stride_to_double'] += 1
            elif self.stride_state == SINGLE_STRIDE:
                self.coverage_database.misc_bins['single_stride_to_double'] += 1

            self.stride_state = DOUBLE_STRIDE
            self.no_strides_count = 0

        if no_stride:
            self.no_strides_count += 1

    def check_latest_strides(self):
        if (len(self.last_values) < 16):
            return

        value_pairs = list(zip(self.last_values, [None] + self.last_values))
        strides = list(map(lambda x: x[0] - x[1], value_pairs[1:]))

        stride_set = set(strides)
        if len(stride_set) == 1:
            self.sample_single_stride_coverage(next(iter(stride_set)))
        elif len(stride_set) == 2:
            first_strides = [s for (i, s) in enumerate(strides) if i % 2 == 0]
            second_strides = [s for (i, s) in enumerate(strides) if i % 2 == 1]

            first_stride_set = set(first_strides)
            second_stride_set = set(second_strides)

            if len(first_stride_set) == 1 and len(second_stride_set) == 1:
                self.sample_double_stride_coverage(next(iter(first_stride_set)),
                        next(iter(second_stride_set)))
            else:
                self.no_strides_count += 1
        else:
            self.no_strides_count += 1

        if self.no_strides_count > 16:
            self.stride_state = NO_STRIDE

async def do_reset(dut):
    dut.rst_ni.value = 1
    await Timer(15, units="ns")

    dut.rst_ni.value = 0
    await ClockCycles(dut.clk_i, 3)
    await Timer(5, units="ns")

    dut.rst_ni.value = 1

# Produces the stimulus for the testbench based on observed coverage
class SimulationController:
    def __init__(self, dut, coverage_monitor, zmq_addr):
        self.dut = dut
        self.coverage_monitor = coverage_monitor
        self.end_simulation_event = Event()
        self.zmq_context = zmq.Context()
        self.zmq_addr = zmq_addr

    # Handles driving a new_value when one is provided by `determine_next_value`
    async def controller_loop(self):
        with self.zmq_context.socket(zmq.REP) as socket:
            socket.bind(self.zmq_addr)

            await ClockCycles(self.dut.clk_i, 1)
            await ReadWrite()

            while(True):
                stimulus_msg = socket.recv()
                stimulus_obj = pickle.loads(stimulus_msg)

                if not isinstance(stimulus_obj, Stimulus):
                    assert False, "Saw bad stimulus message"

                dut_state = self.sample_dut_state()

                if stimulus_obj.value is None:
                    self.dut.valid_i.value = 0
                    self.dut.value_i.value = 0xbaaddead
                else:
                    self.dut.valid_i.value = 1
                    self.dut.value_i.value = stimulus_obj.value

                await ClockCycles(self.dut.clk_i, 1)
                await ReadWrite()

                self.coverage_monitor.sample_coverage()
                socket.send_pyobj((dut_state,
                    self.coverage_monitor.coverage_database))

                if stimulus_obj.finish:
                    self.end_simulation_event.set()
                    break

    def sample_dut_state(self):
        return DUTState(
                last_value = self.dut.last_value.value,

                stride_1 = self.dut.stride_1_q.value,
                stride_1_confidence = self.dut.stride_1_confidence_q.value,

                stride_2 = self.dut.stride_2_q.value,
                stride_2_state = self.dut.stride_2_state_q.value,
                stride_2_confidence = [self.dut.stride_2_confidence_q[0].value,
                                       self.dut.stride_2_confidence_q[1].value]
        )


    def close(self):
        self.zmq_context.term()

    def run_controller(self):
        cocotb.start_soon(self.controller_loop())

@cocotb.test()
async def basic_test(dut):
    coverage_monitor = CoverageMonitor(dut)
    dut.valid_i.value = 0

    cocotb.start_soon(Clock(dut.clk_i, 10, units="ns").start())
    await do_reset(dut)

    with closing(SimulationController(dut, coverage_monitor, "tcp://*:5555")) as simulation_controller:
        simulation_controller.run_controller()

        # Wait for end of simulation to be signalled. Give the design a few more
        # clocks to run before outputting final coverage values
        await simulation_controller.end_simulation_event.wait()
        await ClockCycles(dut.clk_i, 5)

        coverage_monitor.coverage_database.output_coverage()
