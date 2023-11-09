# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass
from typing import Optional
from pprint import pprint

@dataclass
class CoverageDatabase:
    alu_ops: dict[str, int]
    alu_imm_ops: dict[str, int]
    misc: dict[str, int]
    read_reg_a: list[int]
    read_reg_b: list[int]
    write_reg: list[int]
    load_ops: dict[str, int]
    store_ops: dict[str, int]

    alu_ops_x_read_reg_a: dict[str, list[int]]
    alu_ops_x_read_reg_b: dict[str, list[int]]
    alu_ops_x_write_reg: dict[str, list[int]]

    alu_imm_ops_x_read_reg_a: dict[str, list[int]]
    alu_imm_ops_x_write_reg: dict[str, list[int]]

    load_ops_x_read_reg_a: dict[str, list[int]]
    load_ops_x_write_reg: dict[str, list[int]]

    store_ops_x_read_reg_a: dict[str, list[int]]
    store_ops_x_read_reg_b: dict[str, list[int]]


    @classmethod
    def create(cls, alu_op_names, mem_size_names):
        alu_ops_x_read_reg_a = dict.fromkeys(alu_op_names, None)
        alu_ops_x_read_reg_b = dict.fromkeys(alu_op_names, None)
        alu_ops_x_write_reg = dict.fromkeys(alu_op_names, None)

        alu_imm_ops_x_read_reg_a = dict.fromkeys(alu_op_names, None)
        alu_imm_ops_x_write_reg = dict.fromkeys(alu_op_names, None)

        load_ops_x_read_reg_a = dict.fromkeys(mem_size_names, None)
        load_ops_x_write_reg = dict.fromkeys(mem_size_names, None)

        store_ops_x_read_reg_a = dict.fromkeys(mem_size_names, None)
        store_ops_x_read_reg_b = dict.fromkeys(mem_size_names, None)

        for k in alu_op_names:
            alu_ops_x_read_reg_a[k] = [0] * 32
            alu_ops_x_read_reg_b[k] = [0] * 32
            alu_ops_x_write_reg[k] = [0] * 32

            alu_imm_ops_x_read_reg_a[k] = [0] * 32
            alu_imm_ops_x_write_reg[k] = [0] * 32

        for k in mem_size_names:
            load_ops_x_read_reg_a[k] = [0] * 32
            load_ops_x_write_reg[k] = [0] * 32

            store_ops_x_read_reg_a[k] = [0] * 32
            store_ops_x_read_reg_b[k] = [0] * 32

        return cls(alu_ops = dict.fromkeys(alu_op_names, 0),
            alu_imm_ops = dict.fromkeys(alu_op_names, 0),

            misc = {'illegal_insn': 0},

            read_reg_a = [0] * 32,
            read_reg_b = [0] * 32,
            write_reg = [0] * 32,

            load_ops = dict.fromkeys(mem_size_names, 0),
            store_ops = dict.fromkeys(mem_size_names, 0),

            alu_ops_x_read_reg_a = alu_ops_x_read_reg_a,
            alu_ops_x_read_reg_b = alu_ops_x_read_reg_b,
            alu_ops_x_write_reg = alu_ops_x_write_reg,

            alu_imm_ops_x_read_reg_a = alu_imm_ops_x_read_reg_a,
            alu_imm_ops_x_write_reg = alu_imm_ops_x_write_reg,

            load_ops_x_read_reg_a = load_ops_x_read_reg_a,
            load_ops_x_write_reg = load_ops_x_write_reg,

            store_ops_x_read_reg_a = store_ops_x_read_reg_a,
            store_ops_x_read_reg_b = store_ops_x_read_reg_b
        )

    def update(self, alu_op_seen, alu_imm_op_seen, illegal_insn_seen,
            write_reg_seen, read_reg_a_seen, read_reg_b_seen, load_seen,
            store_seen):

        if illegal_insn_seen:
            self.misc['illegal_insn'] += 1
            return

        if read_reg_a_seen is not None:
            self.read_reg_a[read_reg_a_seen] += 1

        if read_reg_b_seen is not None:
            self.read_reg_b[read_reg_b_seen] += 1

        if write_reg_seen is not None:
            self.write_reg[write_reg_seen] += 1

        if alu_op_seen:
            assert read_reg_a_seen is not None
            assert read_reg_b_seen is not None
            assert write_reg_seen is not None

            self.alu_ops[alu_op_seen] += 1

            self.alu_ops_x_read_reg_a[alu_op_seen][read_reg_a_seen] += 1
            self.alu_ops_x_read_reg_b[alu_op_seen][read_reg_b_seen] += 1
            self.alu_ops_x_write_reg[alu_op_seen][write_reg_seen] += 1

        if alu_imm_op_seen:
            assert read_reg_a_seen is not None
            assert write_reg_seen is not None

            self.alu_imm_ops[alu_imm_op_seen] += 1

            self.alu_imm_ops_x_read_reg_a[alu_imm_op_seen][read_reg_a_seen] += 1
            self.alu_imm_ops_x_write_reg[alu_imm_op_seen][write_reg_seen] += 1

        if load_seen is not None:
            assert read_reg_a_seen is not None
            assert write_reg_seen is not None

            self.load_ops[load_seen] += 1

            self.load_ops_x_read_reg_a[load_seen][read_reg_a_seen] += 1
            self.load_ops_x_write_reg[load_seen][write_reg_seen] += 1

        if store_seen is not None:
            assert read_reg_a_seen is not None
            assert read_reg_b_seen is not None

            self.store_ops[store_seen] += 1

            self.store_ops_x_read_reg_a[store_seen][read_reg_a_seen] += 1
            self.store_ops_x_read_reg_b[store_seen][read_reg_b_seen] += 1

    def output_cross_coverage(self, cross_coverage):
        op_str_width = max(map(lambda x: len(x), cross_coverage.keys()))

        for op, reg_hits in cross_coverage.items():
            padding = ''.join([' '] * (op_str_width - len(op)))
            print(f'{op}{padding}:', end='')
            print(','.join(map(lambda x: f'{x:03d}', reg_hits)))

    def output_coverage(self):
        print("ALU Ops:")
        pprint(self.alu_ops)
        print("ALU Imm Ops:")
        pprint(self.alu_imm_ops)
        print("Load Ops:")
        pprint(self.load_ops)
        print("Store Ops:")
        pprint(self.store_ops)
        print("Read Reg Port A:")
        pprint(self.read_reg_a)
        print("Read Reg Port B:")
        pprint(self.read_reg_b)
        print("Write Reg:")
        pprint(self.write_reg)

        print("\nALU Ops x Read Port A:")
        self.output_cross_coverage(self.alu_ops_x_read_reg_a)
        print("\nALU Ops x Read Port B:")
        self.output_cross_coverage(self.alu_ops_x_read_reg_b)
        print("\nALU Ops x Write:")
        self.output_cross_coverage(self.alu_ops_x_write_reg)

        print("\nALU Imm Ops x Read Port A:")
        self.output_cross_coverage(self.alu_imm_ops_x_read_reg_a)
        print("\nALU Imm Ops x Write:")
        self.output_cross_coverage(self.alu_imm_ops_x_write_reg)

        print("\nLoad Ops x Read Port A:")
        self.output_cross_coverage(self.load_ops_x_read_reg_a)
        print("\nLoad Ops x Write:")
        self.output_cross_coverage(self.load_ops_x_write_reg)

        print("\nStore Ops x Read Port A:")
        self.output_cross_coverage(self.store_ops_x_read_reg_a)
        print("\nStore Ops x Read Port B:")
        self.output_cross_coverage(self.store_ops_x_read_reg_b)

