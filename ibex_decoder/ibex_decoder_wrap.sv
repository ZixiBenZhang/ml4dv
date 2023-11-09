// Copyright lowRISC contributors.
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

module ibex_decoder_wrap(input [31:0] insn_i);
  ibex_decoder#(
    .BranchTargetALU(1)
  ) u_decoder (
    .clk_i               (1'b0),
    .rst_ni              (1'b0),
    .branch_taken_i      (1'b1),
    .instr_first_cycle_i (1'b1),
    .instr_rdata_i       (insn_i),
    .instr_rdata_alu_i   (insn_i),
    .illegal_c_insn_i    (1'b0)
  );
endmodule
