# Copyright Zixi Zhang
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

from abc import abstractmethod

from global_shared_types import *


class BaseAgent:
    @abstractmethod
    def reset(self):
        raise NotImplementedError

    @abstractmethod
    def end_simulation(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ):
        raise NotImplementedError

    @abstractmethod
    def generate_next_value(
        self, dut_state: GlobalDUTState, coverage_database: GlobalCoverageDatabase
    ):
        raise NotImplementedError
