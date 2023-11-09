# Copyright Zixi Zhang
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from agents.agent_base import *
from ibex_cpu.shared_types import IbexStateInfo


# 00100080 00a00293
# 00100084 01400313
# 00100088 00000393
# 0010008c 006383b3
# 00100090 fff28293
# 00100094 fe029ce3
# 0010008c 006383b3
# 00100090 fff28293
# 00100094 fe029ce3
# 0010008c 006383b3
# 00100090 fff28293
# 00100094 fe029ce3
# 0010008c 006383b3
# 00100090 fff28293
# 00100094 fe029ce3
# 0010008c 006383b3
# 00100090 fff28293
# 00100094 fe029ce3
# 0010008c 006383b3
# 00100090 fff28293
# 00100094 fe029ce3
# 0010008c 006383b3
# 00100090 fff28293
# 00100094 fe029ce3
# 0010008c 006383b3
# 00100090 fff28293
# 00100094 fe029ce3
# 0010008c 006383b3
# 00100090 fff28293
# 00100094 fe029ce3
# 0010008c 006383b3
# 00100090 fff28293
# 00100094 fe029ce3
# 00100098 0000006f
# add seen: 10, zero_dst: 0, zero_src: 0, same_src: 0
# sub seen: 0, zero_dst: 0, zero_src: 0, same_src: 0
# sll seen: 0, zero_dst: 0, zero_src: 0, same_src: 0
# slt seen: 0, zero_dst: 0, zero_src: 0, same_src: 0
# sltu seen: 0, zero_dst: 0, zero_src: 0, same_src: 0
# xor seen: 0, zero_dst: 0, zero_src: 0, same_src: 0
# srl seen: 0, zero_dst: 0, zero_src: 0, same_src: 0
# sra seen: 0, zero_dst: 0, zero_src: 0, same_src: 0
# or seen: 0, zero_dst: 0, zero_src: 0, same_src: 0
# and seen: 0, zero_dst: 0, zero_src: 0, same_src: 0


class DumbAgent4IC(BaseAgent):
    def __init__(self):
        super().__init__()

    def reset(self):
        pass

    def end_simulation(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ) -> bool:
        ibex_state = dut_state.get()
        if ibex_state is None:
            return False
        ibex_state: IbexStateInfo
        return ibex_state.last_pc == 0x100080 + 0x18

    def generate_next_value(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ) -> List[Tuple[int, int]]:
        return []
