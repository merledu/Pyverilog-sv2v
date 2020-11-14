module TOP(CLK, RST, IN, IN2, reg1, OUT);
  input CLK, RST, IN, IN2;
  reg reg1,reg2,reg3;
  output reg1,OUT;
  wire in1;
  logic OUT,OUTOUT;
  logic IN,IN2;

  always @(posedge CLK or negedge RST) begin
    if(RST) begin
      reg1 <= 1'b0;
    end else begin
      reg1 <= IN;
    end
  end

  always @(posedge CLK or negedge RST) begin
    if(RST) begin
      reg2 <= 1'b0;
    end else begin
      reg2 <= func1(reg1);
    end
  end

  SUB sub(.*);

endmodule

module SUB(CLK,RST,IN, OUT);
  input CLK, RST, IN;
  output OUT;
  reg reg1;
  logic IN;

endmodule

