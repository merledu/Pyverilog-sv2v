# Pyverilog-sv2v
Pyverilog-sv2v is converting systemverilog code to verilog code. The converted script in verilog is used in pyverilog and pyverilog_toolbox that does not correspond to the systemverilog.

Introduction
==============================
This repository consists of two parts. The part is converting systemverilog file to verilog. The script is aimed to preprocess systemverilog for a software (pyverilog, pyverilog_toolbox) that does not correspond to the systemverilog. The second part is to use that converted script in pyverilog which is Python-based Hardware Design Processing Toolkit for Verilog HDL

What's Pyverilog?
==============================

Pyverilog is an open-source hardware design processing toolkit for Verilog HDL. All source codes are written in Python.

Pyverilog includes **(1) code parser, (2) dataflow analyzer, (3) control-flow analyzer and (4) code generator**.
You can create your own design analyzer, code translator and code generator of Verilog HDL based on this toolkit.

Installation
==============================

Requirements
--------------------

- Python3: 3.6 or later
- Icarus Verilog: 10.1 or later

```
sudo apt install iverilog
```

- Jinja2: 2.10 or later
- PLY: 3.4 or later

```
pip3 install jinja2 ply
```

Optional installation for testing
--------------------

These are required for automatic testing of **tests**.
We recommend to install these testing library to verify experimental features.

- pytest: 3.8.1 or later
- pytest-pythonpath: 0.7.3 or later

```
pip3 install pytest pytest-pythonpath
```

Optional installation for visualization
--------------------

These are required for graph visualization by dataflow/graphgen.py and controlflow/controlflow_analyzer.py.

- Graphviz: 2.38.0 or later
- Pygraphviz: 1.3.1 or later

```
sudo apt install graphviz
pip3 install pygraphviz
```

Install
--------------------

Now you can install Pyverilog using setup.py script:

```
python3 setup.py install
```


Tools
==============================

This software includes various tools for Systemverilog HDL design.

* sv2v: converts systemverilog file to verilog
* vparser: Code parser to generate AST (Abstract Syntax Tree) from source codes of Verilog HDL.
* dataflow: Dataflow analyzer with an optimizer to remove redundant expressions and some dataflow handling tools.
* controlflow: Control-flow analyzer with condition analyzer that identify when a signal is activated.
* ast\_code\_generator: Verilog HDL code generator from AST.


Getting Started
==============================

First, please prepare a systemverilog source file and pass it from sv2v converter by writing the command:

python sv2v.py *systemverilog-file-name.sv*

You will get *systemverilog-file-name.v*.

Features of sv2v converter
==============================
logic: Convert to reg or wire.

bit: Convert to reg or wire.

byte: Convert to reg [7:0] or wire [7:0] .

enum: Expand to localparam.

e.g. 
```verilog
enum logic [2:0] {PINK,GREEN,YELLOW=5,BLUE} color_e;
```
->
```verilog
localparam PINK = 'd 0 ;localparam GREEN = 'd 1 ;localparam YELLOW = 'd 5 ;localparam BLUE = 'd 6 ;
```


(.*) port assign: Expand to assignment using port name.

clocking-endcloclking, property-endproperty, sequence-endsequence block: Delete all sentence.

default, assert: Delete line.

always_comb-> always @*

always_latch-> always @*

always_ff-> always

int-> integer

shortint-> reg signed [15:0]

longint-> reg signed [63:0]

'0-> 'd0

'1-> hffff

parameter logic-> parameter

localparam logic-> localparam

function logic-> function


Code parser
------------------------------

Let's try syntax analysis. Please type the command as below.

```
python3 pyverilog/examples/example_parser.py *systemverilog-file-name.v*
```

Dataflow analyzer
------------------------------

Let's try dataflow analysis. Please type the command as below.

```
python3 pyverilog/examples/example_dataflow_analyzer.py -t top *systemverilog-file-name.v* 
```

Let's view the result of dataflow analysis as a picture file. Now we select 'led' as the target. Please type the command as below. In this example, Graphviz and Pygraphviz are installed.

```
python3 pyverilog/examples/example_graphgen.py -t top -s top.led *systemverilog-file-name.v* 
```

Then you got a png file (out.png). The picture shows that the definition of 'led' is a part-selection of 'count' from 23-bit to 16-bit.

![out.png](img/out.png)

Control-flow analyzer
------------------------------

Let's try control-flow analysis. Please type the command as below. In this example, Graphviz and Pygraphviz are installed. If don't use Graphviz, please append "--nograph" option.

```
python3 pyverilog/examples/example_controlflow_analyzer.py -t top *systemverilog-file-name.v*
```
You got also a png file (top_state.png), if you did not append "--nograph". The picture shows that the graphical structure of the state machine.

![top_state.png](img/top_state.png)

Code generator
------------------------------
 
Finally, let's try code generation. Please prepare a Python script as below. The file name is 'test.py'.
A Verilog HDL code is represented by using the AST classes defined in 'vparser.ast'.

```python
from __future__ import absolute_import
from __future__ import print_function
import sys
import os
import pyverilog.vparser.ast as vast
from pyverilog.ast_code_generator.codegen import ASTCodeGenerator

def main():
    datawid = vast.Parameter( 'DATAWID', vast.Rvalue(vast.IntConst('32')) )
    params = vast.Paramlist( [datawid] )
    clk = vast.Ioport( vast.Input('CLK') )
    rst = vast.Ioport( vast.Input('RST') )
    width = vast.Width( vast.IntConst('7'), vast.IntConst('0') )
    led = vast.Ioport( vast.Output('led', width=width) )
    ports = vast.Portlist( [clk, rst, led] )

    width = vast.Width( vast.Minus(vast.Identifier('DATAWID'), vast.IntConst('1')), vast.IntConst('0') )
    count = vast.Reg('count', width=width)

    assign = vast.Assign(
        vast.Lvalue(vast.Identifier('led')), 
        vast.Rvalue(
            vast.Partselect(
                vast.Identifier('count'), # count
                vast.Minus(vast.Identifier('DATAWID'), vast.IntConst('1')), # [DATAWID-1:
                vast.Minus(vast.Identifier('DATAWID'), vast.IntConst('8'))))) # :DATAWID-8]

    sens = vast.Sens(vast.Identifier('CLK'), type='posedge')
    senslist = vast.SensList([ sens ])

    assign_count_true = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('count')),
        vast.Rvalue(vast.IntConst('0')))
    if0_true = vast.Block([ assign_count_true ])

    # count + 1
    count_plus_1 = vast.Plus(vast.Identifier('count'), vast.IntConst('1'))
    assign_count_false = vast.NonblockingSubstitution(
        vast.Lvalue(vast.Identifier('count')),
        vast.Rvalue(count_plus_1))
    if0_false = vast.Block([ assign_count_false ])

    if0 = vast.IfStatement(vast.Identifier('RST'), if0_true, if0_false)
    statement = vast.Block([ if0 ])

    always = vast.Always(senslist, statement)

    items = []
    items.append(count)
    items.append(assign)
    items.append(always)

    ast = vast.ModuleDef("top", params, ports, items)
    
    codegen = ASTCodeGenerator()
    rslt = codegen.visit(ast)
    print(rslt)

if __name__ == '__main__':
    main()
```

Please type the command as below at the same directory with Pyverilog.

```
python3 test.py
```

Then Verilog HDL code generated from the AST instances is displayed.

```verilog
module top #
(
  parameter DATAWID = 32
)
(
  input CLK,
  input RST,
  output [7:0] led
);

  reg [DATAWID-1:0] count;
  assign led = count[DATAWID-1:DATAWID-8];

  always @(posedge CLK) begin
    if(RST) begin
      count <= 0;
    end else begin
      count <= count + 1;
    end
  end


endmodule
```
