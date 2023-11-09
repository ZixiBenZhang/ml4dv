# Copyright lowRISC contributors.
# Licensed under the Apache License, Version 2.0, see LICENSE for details.
# SPDX-License-Identifier: Apache-2.0
# Makefile

# defaults
SIM ?= verilator
TOPLEVEL_LANG ?= verilog

VERILOG_SOURCES += $(PWD)/src/lowrisc_lint_common_0.1/tools/verilator/common.vlt \
	$(PWD)/src/lowrisc_prim_assert_0.1/lint/prim_assert.vlt \
	$(PWD)/src/lowrisc_prim_generic_clock_gating_0/lint/prim_generic_clock_gating.vlt \
	$(PWD)/src/lowrisc_prim_xilinx_clock_gating_0/lint/prim_xilinx_clock_gating.vlt \
	$(PWD)/src/lowrisc_prim_xilinx_clock_mux2_0/lint/prim_xilinx_clock_mux2.vlt \
	$(PWD)/src/lowrisc_prim_cipher_0/lint/prim_cipher.vlt \
	$(PWD)/src/lowrisc_prim_generic_clock_mux2_0/lint/prim_generic_clock_mux2.vlt \
	$(PWD)/src/lowrisc_prim_generic_ram_1p_0/lint/prim_generic_ram_1p.vlt \
	$(PWD)/src/lowrisc_prim_onehot_check_0/lint/prim_onehot_check.vlt \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/lint/verilator_waiver.vlt \
	$(PWD)/src/lowrisc_prim_ram_1p_scr_0.1/lint/prim_ram_1p_scr.vlt \
	$(PWD)/src/lowrisc_ibex_ibex_top_0.1/lint/verilator_waiver.vlt \
	$(PWD)/src/lowrisc_ibex_ibex_pkg_0.1/rtl/ibex_pkg.sv \
	$(PWD)/src/lowrisc_prim_abstract_prim_pkg_0.1/prim_pkg.sv \
	$(PWD)/src/lowrisc_prim_ram_1p_pkg_0/rtl/prim_ram_1p_pkg.sv \
	$(PWD)/src/lowrisc_prim_cipher_pkg_0.1/rtl/prim_cipher_pkg.sv \
	$(PWD)/src/lowrisc_prim_generic_buf_0/rtl/prim_generic_buf.sv \
	$(PWD)/src/lowrisc_prim_generic_clock_gating_0/rtl/prim_generic_clock_gating.sv \
	$(PWD)/src/lowrisc_prim_generic_flop_0/rtl/prim_generic_flop.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_pkg.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_22_16_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_22_16_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_28_22_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_28_22_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_39_32_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_39_32_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_64_57_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_64_57_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_72_64_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_72_64_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_22_16_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_22_16_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_39_32_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_39_32_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_72_64_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_72_64_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_76_68_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_hamming_76_68_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_22_16_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_22_16_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_28_22_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_28_22_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_39_32_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_39_32_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_64_57_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_64_57_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_72_64_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_72_64_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_22_16_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_22_16_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_39_32_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_39_32_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_72_64_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_72_64_enc.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_76_68_dec.sv \
	$(PWD)/src/lowrisc_prim_secded_0.1/rtl/prim_secded_inv_hamming_76_68_enc.sv \
	$(PWD)/src/lowrisc_prim_xilinx_buf_0/rtl/prim_xilinx_buf.sv \
	$(PWD)/src/lowrisc_prim_xilinx_clock_gating_0/rtl/prim_xilinx_clock_gating.sv \
	$(PWD)/src/lowrisc_prim_xilinx_clock_mux2_0/rtl/prim_xilinx_clock_mux2.sv \
	$(PWD)/src/lowrisc_prim_xilinx_flop_0/rtl/prim_xilinx_flop.sv \
	$(PWD)/src/lowrisc_ibex_ibex_icache_0.1/rtl/ibex_icache.sv \
  $(PWD)/src/lowrisc_ibex_ibex_tracer_0.1/rtl/ibex_tracer_pkg.sv \
  $(PWD)/src/lowrisc_ibex_ibex_tracer_0.1/rtl/ibex_tracer.sv \
	$(PWD)/src/lowrisc_prim_abstract_buf_0/prim_buf.sv \
	$(PWD)/src/lowrisc_prim_abstract_clock_gating_0/prim_clock_gating.sv \
	$(PWD)/src/lowrisc_prim_abstract_flop_0/prim_flop.sv \
	$(PWD)/src/lowrisc_prim_cipher_0/rtl/prim_subst_perm.sv \
	$(PWD)/src/lowrisc_prim_cipher_0/rtl/prim_present.sv \
	$(PWD)/src/lowrisc_prim_cipher_0/rtl/prim_prince.sv \
	$(PWD)/src/lowrisc_prim_generic_clock_mux2_0/rtl/prim_generic_clock_mux2.sv \
	$(PWD)/src/lowrisc_prim_generic_ram_1p_0/rtl/prim_generic_ram_1p.sv \
	$(PWD)/src/lowrisc_prim_lfsr_0.1/rtl/prim_lfsr.sv \
	$(PWD)/src/lowrisc_prim_util_0.1/rtl/prim_util_pkg.sv \
	$(PWD)/src/lowrisc_prim_abstract_clock_mux2_0/prim_clock_mux2.sv \
	$(PWD)/src/lowrisc_prim_badbit_ram_1p_0/prim_badbit_ram_1p.sv \
	$(PWD)/src/lowrisc_prim_onehot_check_0/rtl/prim_onehot_check.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_alu.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_branch_predict.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_compressed_decoder.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_controller.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_cs_registers.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_csr.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_counter.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_decoder.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_ex_block.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_fetch_fifo.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_id_stage.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_if_stage.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_load_store_unit.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_multdiv_fast.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_multdiv_slow.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_prefetch_buffer.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_pmp.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_wb_stage.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_dummy_instr.sv \
	$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl/ibex_core.sv \
	$(PWD)/src/lowrisc_prim_abstract_ram_1p_0/prim_ram_1p.sv \
	$(PWD)/src/lowrisc_prim_ram_1p_adv_0.1/rtl/prim_ram_1p_adv.sv \
	$(PWD)/src/lowrisc_prim_ram_1p_scr_0.1/rtl/prim_ram_1p_scr.sv \
	$(PWD)/src/lowrisc_ibex_ibex_top_0.1/rtl/ibex_register_file_ff.sv \
	$(PWD)/src/lowrisc_ibex_ibex_top_0.1/rtl/ibex_register_file_fpga.sv \
	$(PWD)/src/lowrisc_ibex_ibex_top_0.1/rtl/ibex_register_file_latch.sv \
	$(PWD)/src/lowrisc_ibex_ibex_top_0.1/rtl/ibex_lockstep.sv \
	$(PWD)/src/lowrisc_ibex_ibex_top_0.1/rtl/ibex_top.sv \
  $(PWD)/src/lowrisc_ibex_ibex_top_tracing_0.1/rtl/ibex_top_tracing.sv \
	$(PWD)/cocotb_ibex.sv
# use VHDL_SOURCES for VHDL files

# TOPLEVEL is the name of the toplevel module in your Verilog or VHDL file
TOPLEVEL = cocotb_ibex

# MODULE is the basename of the Python test file
MODULE = cocotb_ibex

#--trace-fst --trace-structs \

EXTRA_ARGS +=  \
	+incdir+$(PWD)/src/lowrisc_dv_crypto_prince_ref_0.1 \
	-CFLAGS -I$(PWD)/src/lowrisc_dv_crypto_prince_ref_0.1 \
	+incdir+$(PWD)/src/lowrisc_dv_dv_fcov_macros_0 \
	-CFLAGS -I$(PWD)/src/lowrisc_dv_dv_fcov_macros_0 \
	+incdir+$(PWD)/src/lowrisc_dv_secded_enc_0 \
	-CFLAGS -I$(PWD)/src/lowrisc_dv_secded_enc_0 \
	+incdir+$(PWD)/src/lowrisc_prim_util_get_scramble_params_0/rtl \
	-CFLAGS -I$(PWD)/src/lowrisc_prim_util_get_scramble_params_0/rtl \
	+incdir+$(PWD)/src/lowrisc_prim_util_memload_0/rtl \
	-CFLAGS -I$(PWD)/src/lowrisc_prim_util_memload_0/rtl \
	+incdir+$(PWD)/src/lowrisc_dv_scramble_model_0 \
	-CFLAGS -I$(PWD)/src/lowrisc_dv_scramble_model_0 \
	+incdir+$(PWD)/src/lowrisc_dv_verilator_memutil_dpi_0/cpp \
	-CFLAGS -I$(PWD)/src/lowrisc_dv_verilator_memutil_dpi_0/cpp \
	+incdir+$(PWD)/src/lowrisc_dv_verilator_memutil_dpi_scrambled_0/cpp \
	-CFLAGS -I$(PWD)/src/lowrisc_dv_verilator_memutil_dpi_scrambled_0/cpp \
	+incdir+$(PWD)/src/lowrisc_prim_assert_0.1/rtl \
	-CFLAGS -I$(PWD)/src/lowrisc_prim_assert_0.1/rtl \
	+incdir+$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl \
	-CFLAGS -I$(PWD)/src/lowrisc_ibex_ibex_core_0.1/rtl \
  -DSYNTHESIS=1 \
  -DRVFI=1 \
	--trace-fst \
  --trace-structs \
	-Wno-fatal \
  -CFLAGS "-std=c++14 -Wall -O3"


# include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim
