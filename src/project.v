/* Copyright (c) 2026 Rithvik Vadlamani
 * SPDX-License-Identifier: Apache-2.0
 */
`default_nettype none

module tt_um_rithvik_deltatile (
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    // Commands are sampled on each enabled rising edge with strobe high.
    localparam [2:0] NOP = 3'd0, CLEAR = 3'd1, LOAD_A = 3'd2,
                     MAC = 3'd3, READ = 3'd4, CLEAR_ERROR = 3'd5;
    wire [2:0] command = uio_in[2:0];
    wire strobe = uio_in[3];
    wire clear = strobe && (command == CLEAR);
    reg [7:0] staged_a;
    reg a_pending, error;
    reg [2:0] read_select;
    reg valid1, valid2;
    wire busy = valid1 || valid2;
    wire launch = strobe && (command == MAC) && a_pending;

    // Skew row 1 / column 1 by one cycle, then forward to PE11.
    reg signed [3:0] a0_right, a1_skew, b0_down, b1_skew;
    reg signed [3:0] a1_right, b1_down;
    reg signed [11:0] c00, c01, c10, c11;
    wire signed [3:0] a0 = staged_a[3:0];
    wire signed [3:0] a1 = staged_a[7:4];
    wire signed [3:0] b0 = ui_in[3:0];
    wire signed [3:0] b1 = ui_in[7:4];
    wire signed [7:0] p00 = a0 * b0;
    wire signed [7:0] p01 = a0_right * b1_skew;
    wire signed [7:0] p10 = a1_skew * b0_down;
    wire signed [7:0] p11 = a1_right * b1_down;

    // Data forwarding registers need no reset: valid bits guard every use.
    always @(posedge clk) begin
        if (ena && rst_n && !clear) begin
            if (launch) begin
                a0_right <= a0;
                a1_skew <= a1;
                b0_down <= b0;
                b1_skew <= b1;
            end
            if (valid1) begin
                a1_right <= a1_skew;
                b1_down <= b1_skew;
            end
        end
    end

    always @(posedge clk) begin
        if (!rst_n) begin
            c00 <= 12'sd0;
            c01 <= 12'sd0;
            c10 <= 12'sd0;
            c11 <= 12'sd0;
            valid1 <= 1'b0;
            valid2 <= 1'b0;
            a_pending <= 1'b0;
            error <= 1'b0;
            read_select <= 3'd0;
            staged_a <= 8'd0;
        end else if (ena) begin
            if (clear) begin
                c00 <= 12'sd0;
                c01 <= 12'sd0;
                c10 <= 12'sd0;
                c11 <= 12'sd0;
                valid1 <= 1'b0;
                valid2 <= 1'b0;
                a_pending <= 1'b0;
                error <= 1'b0;
                read_select <= 3'd0;
            end else begin
                valid1 <= launch;
                valid2 <= valid1;
                if (launch) c00 <= c00 + {{4{p00[7]}}, p00};
                if (valid1) begin
                    c01 <= c01 + {{4{p01[7]}}, p01};
                    c10 <= c10 + {{4{p10[7]}}, p10};
                end
                if (valid2) c11 <= c11 + {{4{p11[7]}}, p11};
                if (strobe) begin
                    case (command)
                        NOP: begin end
                        LOAD_A: begin
                            staged_a <= ui_in;
                            a_pending <= 1'b1;
                        end
                        MAC: begin
                            if (a_pending) a_pending <= 1'b0;
                            else error <= 1'b1;
                        end
                        READ: begin
                            if (!busy && !a_pending) read_select <= ui_in[2:0];
                            else error <= 1'b1;
                        end
                        CLEAR_ERROR: error <= 1'b0;
                        default: error <= 1'b1;
                    endcase
                end
            end
        end
    end

    reg signed [11:0] selected_score;
    always @* begin
        case (read_select[2:1])
            2'd0: selected_score = c00;
            2'd1: selected_score = c01;
            2'd2: selected_score = c10;
            default: selected_score = c11;
        endcase
    end
    assign uo_out = read_select[0]
                  ? {{4{selected_score[11]}}, selected_score[11:8]}
                  : selected_score[7:0];
    assign uio_oe = 8'hf0;
    assign uio_out = {ena && !busy && !a_pending, error, busy, ena, 4'b0000};
    wire _unused = &{uio_in[7:4], 1'b0};
endmodule
