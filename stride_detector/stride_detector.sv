// Copyright lowRISC contributors.
// Licensed under the Apache License, Version 2.0, see LICENSE for details.
// SPDX-License-Identifier: Apache-2.0

module stride_detector #(parameter MAX_STRIDE_WIDTH=5) (
  input clk_i,
  input rst_ni,

  input logic [31:0] value_i,
  input logic        valid_i,

  output logic [MAX_STRIDE_WIDTH-1:0] stride_1_o,
  output logic                        stride_1_valid_o,
  output logic [MAX_STRIDE_WIDTH-1:0] stride_2_o,
  output logic                        stride_2_valid_o
);

  typedef enum logic {
    STATE_SECOND_STRIDE,
    STATE_FIRST_STRIDE
  } state_e;

  state_e stride_2_state_q, stride_2_state_d;

  logic [1:0] stride_1_confidence_d, stride_1_confidence_q;

  logic [1:0] stride_2_confidence_d[2], stride_2_confidence_q[2];

  logic [31:0]                 last_value;
  logic [MAX_STRIDE_WIDTH-1:0] stride_1_d, stride_2_d[2];
  logic [MAX_STRIDE_WIDTH-1:0] stride_1_q, stride_2_q[2];
  logic [32:0]                 incoming_stride_full;
  logic [MAX_STRIDE_WIDTH-1:0] incoming_stride;
  logic                        incoming_stride_overflow;

  assign incoming_stride_full = value_i - last_value;

  assign incoming_stride_overflow =
    incoming_stride_full[MAX_STRIDE_WIDTH-1] ? ~&incoming_stride_full[32:MAX_STRIDE_WIDTH] :
                                                |incoming_stride_full[32:MAX_STRIDE_WIDTH];

  assign incoming_stride = incoming_stride_full[MAX_STRIDE_WIDTH-1:0];

  always_comb begin
    stride_1_confidence_d = stride_1_confidence_q;
    stride_1_d            = stride_1_q;

    if (valid_i) begin
      if ((incoming_stride == stride_1_q) && !incoming_stride_overflow) begin
        if (stride_1_confidence_q < 2'b11) begin
          stride_1_confidence_d = stride_1_confidence_q + 2'b1;
        end
      end else if (stride_1_confidence_q > 0) begin
        stride_1_confidence_d = stride_1_confidence_q - 2'b1;
      end else begin
        stride_1_d = incoming_stride;
      end
    end
  end

  always_comb begin
    stride_2_d[0] = stride_2_q[0];
    stride_2_d[1] = stride_2_q[1];

    stride_2_confidence_d[0] = stride_2_confidence_q[0];
    stride_2_confidence_d[1] = stride_2_confidence_q[1];

    stride_2_state_d = stride_2_state_q;

    if (valid_i) begin
      case (stride_2_state_q)
        STATE_FIRST_STRIDE: begin
          if ((incoming_stride == stride_2_q[0]) && !incoming_stride_overflow) begin
            if (stride_2_confidence_q[0] < 2'b11) begin
              stride_2_confidence_d[0] = stride_2_confidence_q[0] + 2'b1;
            end
          end else if (stride_2_confidence_q[0] > 0) begin
              stride_2_confidence_d[0] = stride_2_confidence_q[0] - 2'b1;
          end else begin
            stride_2_d[0] = incoming_stride;
          end

          stride_2_state_d = STATE_SECOND_STRIDE;
        end
        STATE_SECOND_STRIDE: begin
          if ((incoming_stride == stride_2_q[1]) && !incoming_stride_overflow) begin
            if (stride_2_confidence_q[1] < 2'b11) begin
              stride_2_confidence_d[1] = stride_2_confidence_q[1] + 2'b1;
            end
          end else if (stride_2_confidence_q[1] > 0) begin
            stride_2_confidence_d[1] = stride_2_confidence_q[1] - 2'b1;
          end else begin
            stride_2_d[1] = incoming_stride;
          end

          stride_2_state_d = STATE_FIRST_STRIDE;
        end
      endcase
    end
  end

  always @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      last_value <= '0;
    end else begin
      if (valid_i) begin
        last_value <= value_i;
      end
    end
  end

  always @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      stride_1_q            <= '0;
      stride_1_confidence_q <= '0;
    end else begin
      stride_1_q            <= stride_1_d;
      stride_1_confidence_q <= stride_1_confidence_d;
    end
  end

  always @(posedge clk_i or negedge rst_ni) begin
    if (!rst_ni) begin
      stride_2_q[0] <= '0;
      stride_2_q[1] <= '0;

      stride_2_confidence_q[0] <= '0;
      stride_2_confidence_q[1] <= '0;

      stride_2_state_q <= STATE_FIRST_STRIDE;
    end else begin
      stride_2_q[0] <= stride_2_d[0];
      stride_2_q[1] <= stride_2_d[1];

      stride_2_confidence_q[0] <= stride_2_confidence_d[0];
      stride_2_confidence_q[1] <= stride_2_confidence_d[1];

      stride_2_state_q <= stride_2_state_d;
    end
  end

  assign stride_1_valid_o = (stride_1_confidence_q == 2'b11) || (stride_2_confidence_q[0] == 2'b11);
  assign stride_1_o = stride_1_confidence_q == 2'b11 ? stride_1_q : stride_2_q[0];

  assign stride_2_valid_o = (stride_2_confidence_q[0] == 2'b11) &&
                            (stride_2_confidence_q[1] == 2'b11) &&
                            (stride_1_confidence_q != 2'b11);

  assign stride_2_o = stride_2_q[1];
endmodule

