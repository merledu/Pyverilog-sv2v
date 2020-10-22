from __future__ import absolute_import
from __future__ import print_function
import os
import sys
from pyverilog.vparser.parser import VerilogCodeParser

try:
    from StringIO import StringIO
except:
    from io import StringIO

codedir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + '/verilogcode/'

expected = """\
Source:  (at 1)
  Description:  (at 1)
    ModuleDef: TOP (at 1)
      Paramlist:  (at 0)
      Portlist:  (at 2)
        Ioport:  (at 3)
          Input: CLK, False (at 3)
        Ioport:  (at 4)
          Input: RST, False (at 4)
        Ioport:  (at 5)
          Output: LED, False (at 5)
            Width:  (at 5)
              IntConst: 7 (at 5)
              IntConst: 0 (at 5)
      InstanceList: led (at 9)
        Instance: inst_led, led (at 9)
          PortArg: CLK (at 14)
            Identifier: CLK (at 14)
          PortArg: RST (at 15)
            Identifier: RST (at 15)
          PortArg: LED (at 16)
            Identifier: LED (at 16)
    ModuleDef: led (at 21)
      Paramlist:  (at 21)
        Decl:  (at 23)
          Parameter: STEP, False (at 23)
            Rvalue:  (at 23)
              IntConst: 10 (at 23)
      Portlist:  (at 25)
        Ioport:  (at 26)
          Input: CLK, False (at 26)
        Ioport:  (at 27)
          Input: RST, False (at 27)
        Ioport:  (at 28)
          Output: LED, False (at 28)
            Width:  (at 28)
              IntConst: 7 (at 28)
              IntConst: 0 (at 28)
          Reg: LED, False (at 28)
            Width:  (at 28)
              IntConst: 7 (at 28)
              IntConst: 0 (at 28)
      Decl:  (at 31)
        Reg: count, False (at 31)
          Width:  (at 31)
            IntConst: 31 (at 31)
            IntConst: 0 (at 31)
      Always:  (at 33)
        SensList:  (at 33)
          Sens: posedge (at 33)
            Identifier: CLK (at 33)
        Block: None (at 33)
          IfStatement:  (at 34)
            Identifier: RST (at 34)
            Block: None (at 34)
              NonblockingSubstitution:  (at 35)
                Lvalue:  (at 35)
                  Identifier: count (at 35)
                Rvalue:  (at 35)
                  IntConst: 0 (at 35)
              NonblockingSubstitution:  (at 36)
                Lvalue:  (at 36)
                  Identifier: LED (at 36)
                Rvalue:  (at 36)
                  IntConst: 0 (at 36)
            Block: None (at 37)
              IfStatement:  (at 38)
                Eq:  (at 38)
                  Identifier: count (at 38)
                  Minus:  (at 38)
                    Identifier: STEP (at 38)
                    IntConst: 1 (at 38)
                Block: None (at 38)
                  NonblockingSubstitution:  (at 39)
                    Lvalue:  (at 39)
                      Identifier: count (at 39)
                    Rvalue:  (at 39)
                      IntConst: 0 (at 39)
                  NonblockingSubstitution:  (at 40)
                    Lvalue:  (at 40)
                      Identifier: LED (at 40)
                    Rvalue:  (at 40)
                      Plus:  (at 40)
                        Identifier: LED (at 40)
                        IntConst: 1 (at 40)
                Block: None (at 41)
                  NonblockingSubstitution:  (at 42)
                    Lvalue:  (at 42)
                      Identifier: count (at 42)
                    Rvalue:  (at 42)
                      Plus:  (at 42)
                        Identifier: count (at 42)
                        IntConst: 1 (at 42)
"""

def test():
    filelist = [codedir + 'instance_empty_params.v']
    output = 'preprocess.out'
    include = [codedir]
    define = []
    
    parser = VerilogCodeParser(filelist,
                               preprocess_include=include,
                               preprocess_define=define)
    ast = parser.parse()
    directives = parser.get_directives()

    output = StringIO()
    ast.show(buf=output)

    for lineno, directive in directives:
        output.write('Line %d : %s' % (lineno, directive))
    
    rslt = output.getvalue()

    print(rslt)
    assert(expected == rslt)

if __name__ == '__main__':
    test()
