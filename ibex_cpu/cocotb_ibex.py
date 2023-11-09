# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

import struct
import zmq

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer, ClockCycles, ReadWrite, Event
from instruction_monitor import InstructionMonitor
from shared_types import Stimulus, IbexStateInfo

from contextlib import closing


async def do_reset(dut):
    dut.rst_ni.value = 1
    await Timer(15, units="ns")

    dut.rst_ni.value = 0
    await ClockCycles(dut.clk_i, 3)
    await Timer(5, units="ns")

    dut.rst_ni.value = 1

prog = [0x00000293,
        0x01400313,
        0x006282b3,
        0xffdff06f]


class MemAgent:
    def __init__(self, dut, mem_name, default_load_val=0xC0001073, handle_writes=True):
        self.mem_dict = {}

        self.clk = dut.clk_i
        self.gnt = getattr(dut, mem_name + '_gnt_i')
        self.req = getattr(dut, mem_name + '_req_o')
        self.addr = getattr(dut, mem_name + '_addr_o')
        self.rvalid = getattr(dut, mem_name + '_rvalid_i')
        self.rdata = getattr(dut, mem_name + '_rdata_i')

        self.default_load_val = default_load_val

        self.handle_writes = handle_writes

        if handle_writes:
            self.we = getattr(dut, mem_name + '_we_o')
            self.wdata = getattr(dut, mem_name + '_wdata_o')
            self.be = getattr(dut, mem_name + '_be_o')

    def load_bin(self, bin_filename, start_addr):
        with open(bin_filename, 'rb') as bin_file:
            cur_addr = start_addr

            for (word,) in struct.iter_unpack('<I', bin_file.read()):
                self.mem_dict[cur_addr] = word
                cur_addr += 4

    def write_mem(self, addr, word):
        self.mem_dict[addr] = word

    async def run_mem(self):
        self.gnt.value = 0
        self.rvalid.value = 0

        while True:
            await ClockCycles(self.clk, 1)
            await ReadWrite()
            self.rvalid.value = 0

            if (self.req.value):
                self.gnt.value = 1
                access_addr = self.addr.value

                if self.handle_writes and self.we.value:
                    write_data = self.wdata.value
                else:
                    write_data = None

                await ClockCycles(self.clk, 1)
                await ReadWrite()
                self.gnt.value = 0
                self.rvalid.value = 1

                if self.handle_writes and write_data:
                    self.rdata.value = 0xdeadbaad
                    self.mem_dict[int(access_addr)] = int(write_data)
                else:
                    self.rdata.value = self.mem_dict.get(int(access_addr),
                                                         self.default_load_val)


async def update_magic_loc(dut, dmem_agent):
    dmem_agent.mem_dict[0x80000000] = 1

    while True:
        await ClockCycles(dut.clk_i, 1)
        await ReadWrite()

        dmem_agent.mem_dict[0x80000000] += 1


class SimulationController:
    def __init__(self, dut, instruction_monitor, imem_agent, zmq_addr):
        self.dut = dut
        self.instruction_monitor = instruction_monitor
        self.end_simulation_event = Event()
        self.zmq_context = zmq.Context()
        self.zmq_addr = zmq_addr
        self.imem_agent = imem_agent

    async def controller_loop(self):
        with self.zmq_context.socket(zmq.REP) as socket:
            socket.bind(self.zmq_addr)

            await ClockCycles(self.dut.clk_i, 1)
            await ReadWrite()

            while (True):
                stimulus_obj = socket.recv_pyobj()

                if not isinstance(stimulus_obj, Stimulus):
                    assert False, "Saw bad stimulus message"

                for addr, data in stimulus_obj.insn_mem_updates:
                    self.imem_agent.write_mem(addr, data)

                await ClockCycles(self.dut.clk_i, 1)
                await ReadWrite()

                self.instruction_monitor.sample_insn_coverage()

                ibex_state_info = IbexStateInfo(
                    last_pc=self.instruction_monitor.last_pc,
                    last_insn=self.instruction_monitor.last_insn)

                socket.send_pyobj((ibex_state_info,
                                   self.instruction_monitor.coverage_db))

                if stimulus_obj.finish:
                    self.end_simulation_event.set()
                    break

    def close(self):
        self.zmq_context.term()


@cocotb.test()
async def basic_test(dut):

    dut.data_gnt_i.value = 0
    dut.data_rvalid_i.value = 0

    imem_agent = MemAgent(dut, "instr", handle_writes=False)
    dmem_agent = MemAgent(dut, "data", handle_writes=True)
    ins_mon = InstructionMonitor(dut)
    imem_agent.load_bin('test_prog.bin', 0x100080)

    cocotb.start_soon(Clock(dut.clk_i, 10, units="ns").start())
    await do_reset(dut)
    cocotb.start_soon(imem_agent.run_mem())
    cocotb.start_soon(dmem_agent.run_mem())
    cocotb.start_soon(update_magic_loc(dut, dmem_agent))

    await ClockCycles(dut.clk_i, 1)

    sim_ctrl = SimulationController(dut, ins_mon, imem_agent, "tcp://*:5555")
    with closing(sim_ctrl) as simulation_controller:
        cocotb.start_soon(simulation_controller.controller_loop())

        await simulation_controller.end_simulation_event.wait()
        await ClockCycles(dut.clk_i, 1)
