# Makefile
# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0

# defaults
SIM ?= verilator
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/stride_detector.sv
# use VHDL_SOURCES for VHDL files

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = stride_detector

# MODULE is the basename of the Python test file
MODULE = stride_detector_cocotb

COCOTB_LOG_LEVEL = debug

EXTRA_ARGS += --trace-fst --trace-structs \
	-Wno-fatal -CFLAGS "-std=c++14 -Wall -O3"

# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
