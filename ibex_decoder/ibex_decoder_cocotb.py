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

import ibex_consts

class CoverageMonitor:
    alu_op_names = [
            'add',
            'sub',
            'or',
            'xor',
            'and',
            'sll',
            'srl',
            'sra',
            'slt',
            'sltu']

    mem_size_names = [
            'word',
            'half-word',
            'byte']

    def __init__(self, dut):
        self.coverage_database = CoverageDatabase.create(self.alu_op_names,
                self.mem_size_names)

        self.signals = {
                'alu_operator': dut.u_decoder.alu_operator_o,
                'imm_a_mux_sel': dut.u_decoder.imm_a_mux_sel_o,
                'imm_b_mux_sel': dut.u_decoder.imm_b_mux_sel_o,
                'alu_op_a_mux_sel': dut.u_decoder.alu_op_a_mux_sel_o,
                'alu_op_b_mux_sel': dut.u_decoder.alu_op_b_mux_sel_o,
                'rf_we': dut.u_decoder.rf_we_o,
                'rf_waddr': dut.u_decoder.rf_waddr_o,
                'rf_raddr_a': dut.u_decoder.rf_raddr_a_o,
                'rf_raddr_b': dut.u_decoder.rf_raddr_b_o,
                'rf_ren_a': dut.u_decoder.rf_ren_a_o,
                'rf_ren_b': dut.u_decoder.rf_ren_b_o,
                'rf_wdata_sel': dut.u_decoder.rf_wdata_sel_o,
                'mult_sel': dut.u_decoder.mult_sel_o,
                'div_sel': dut.u_decoder.div_sel_o,
                'illegal_insn': dut.u_decoder.illegal_insn_o,
                'data_req': dut.u_decoder.data_req_o,
                'data_we': dut.u_decoder.data_we_o,
                'data_type': dut.u_decoder.data_type_o
        }

        self.write_reg_seen = None
        self.read_reg_a_seen = None
        self.read_reg_b_seen = None
        self.alu_op_seen = None
        self.alu_imm_op_seen = None
        self.store_seen = None
        self.load_seen = None


    def alu_op_str_from_val(self, alu_operator):
        if alu_operator == ibex_consts.ALU_ADD:
            return "add"
        elif alu_operator == ibex_consts.ALU_SUB:
            return "sub"
        elif alu_operator == ibex_consts.ALU_XOR:
            return "xor"
        elif alu_operator == ibex_consts.ALU_OR:
            return "or"
        elif alu_operator == ibex_consts.ALU_AND:
            return "and"
        elif alu_operator == ibex_consts.ALU_SRA:
            return "sra"
        elif alu_operator == ibex_consts.ALU_SRL:
            return "srl"
        elif alu_operator == ibex_consts.ALU_SLL:
            return "sll"
        elif alu_operator == ibex_consts.ALU_SLT:
            return "slt"
        elif alu_operator == ibex_consts.ALU_SLTU:
            return "sltu"

        return None

    def access_size_str_from_type(self, data_type):
        if data_type == 0:
            return "word"
        if data_type == 1:
            return "half-word"
        if data_type == 2:
            return "byte"

        return None

    def clear_seen(self):
        self.alu_op_seen = None
        self.alu_imm_op_seen = None
        self.write_reg_seen = None
        self.read_reg_a_seen = None
        self.read_reg_b_seen = None
        self.store_seen = None
        self.load_seen = None

    def sample_alu_ops(self):

        if (self.signals['rf_we'].value != 0 and
            self.signals['mult_sel'].value == 0 and
            self.signals['div_sel'].value == 0 and
            self.signals['rf_ren_a'].value != 0 and
            self.signals['alu_op_a_mux_sel'].value == ibex_consts.OP_A_REG_A and
            self.signals['rf_wdata_sel'].value == ibex_consts.RF_WD_EX):
                alu_op_str = self.alu_op_str_from_val(self.signals['alu_operator'])
                if alu_op_str:
                    if self.signals['alu_op_b_mux_sel'].value == ibex_consts.OP_B_IMM:
                        self.alu_imm_op_seen = alu_op_str
                    else:
                        self.alu_op_seen = alu_op_str

    def sample_mem_ops(self):
        if self.signals['data_req'].value != 0:
            access_size_str = self.access_size_str_from_type(self.signals['data_type'].value)

            if self.signals['data_we'].value != 0:
                self.store_seen = access_size_str
            else:
                self.load_seen = access_size_str

    def sample_rf_accesses(self):
        if (self.signals['rf_we'].value != 0) or (self.load_seen is not None):
            self.write_reg_seen = self.signals['rf_waddr'].value

        if self.signals['rf_ren_a'].value != 0:
            self.read_reg_a_seen = self.signals['rf_raddr_a'].value

        if self.signals['rf_ren_b'].value != 0:
            self.read_reg_b_seen = self.signals['rf_raddr_b'].value

    def sample_coverage(self):
        illegal_insn = False
        self.clear_seen()

        if self.signals['illegal_insn'].value == 0:
            self.sample_alu_ops()
            self.sample_mem_ops()
            self.sample_rf_accesses()
        else:
            illegal_insn = True

        self.coverage_database.update(alu_op_seen = self.alu_op_seen,
                alu_imm_op_seen = self.alu_imm_op_seen,
                illegal_insn_seen = illegal_insn,
                write_reg_seen = self.write_reg_seen,
                read_reg_a_seen = self.read_reg_a_seen,
                read_reg_b_seen = self.read_reg_b_seen,
                load_seen = self.load_seen,
                store_seen = self.store_seen)

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

            await Timer(5, units="ns")
            await ReadWrite()

            while(True):
                stimulus_msg = socket.recv()
                stimulus_obj = pickle.loads(stimulus_msg)

                if stimulus_obj is None:
                    socket.send_pyobj(self.coverage_monitor.coverage_database)
                    self.end_simulation_event.set()
                    break

                if not isinstance(stimulus_obj, int):
                    assert False, "Saw bad stimulus message"

                if stimulus_obj > 2**32 or stimulus_obj < 0:
                    assert False, "Saw out of range stimulus message"

                self.dut.insn_i.value = stimulus_obj

                await Timer(5, units="ns")
                await ReadWrite()

                self.coverage_monitor.sample_coverage()
                socket.send_pyobj(self.coverage_monitor.coverage_database)

    def close(self):
        self.zmq_context.term()

    def run_controller(self):
        cocotb.start_soon(self.controller_loop())

@cocotb.test()
async def basic_test(dut):
    coverage_monitor = CoverageMonitor(dut)
    dut.insn_i.value = 0

    with closing(SimulationController(dut, coverage_monitor, "tcp://*:5555")) as simulation_controller:
        simulation_controller.run_controller()

        # Wait for end of simulation to be signalled. Give the design a few more
        # clocks to run before outputting final coverage values
        await simulation_controller.end_simulation_event.wait()
        await Timer(5, units="ns")
