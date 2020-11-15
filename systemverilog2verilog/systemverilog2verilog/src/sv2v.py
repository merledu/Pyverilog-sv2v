#-------------------------------------------------------------------------------
# Name:        sv2v
# Purpose:     Converting systemverilog code to verilog code.
#
# Author:      rf
#
# Created:     14/11/2015
# Copyright:   (c) rf 2015
# Licence:     Apache Licence 2.0
#-------------------------------------------------------------------------------

from optparse import OptionParser
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from systemverilog2verilog.src import util
from collections import OrderedDict



def convert2sv(filelist=None, is_testing=False, debug=False):
    optparser = OptionParser()
    (options, args) = optparser.parse_args()
    #TODO interface, struct, union

    if args and not is_testing:
        filelist = args
    elif not filelist:
        raise Exception("Verilog file is not assigned.")

    for file_name in filelist:
        if not os.path.exists(file_name): raise IOError("file not found: " + file_name)

    for file_name in filelist:
        name_without_extension = re.sub("\.[^.]*$", "", file_name)
        comdel_file = name_without_extension + '_comdel.v'
        delete_comments(file_name, comdel_file)

        make_module_info(comdel_file, debug)

        enum_file_name = name_without_extension + '_eexpand.v'
        expand_enum(comdel_file, enum_file_name)
        split_file_name = name_without_extension + '_split.v'
        split_logic_decrarement(enum_file_name, split_file_name)

        sj = skip_judge()
        read_file = open(split_file_name, 'r')
        write_file = open(name_without_extension + '_conv.v', 'w')

        try:
            for line_num, line in enumerate(read_file):
                if line.split() and line.split()[0] == 'module':
                    module_name = get_module_name_from_decline(line)
                    while ';' not in line:
                        line = convert_logic_in_fl(line)
                        write_file.write(line)
                        line = next(read_file) #skip module declarement
                    line = convert_logic_in_fl(line)
                    write_file.write(line)
                    line = next(read_file)

                    module_lines = []
                    while not line.split() or line.split()[0] != 'endmodule':
                        module_lines.append(line)
                        line = next(read_file)
                    while module_lines:
                        skip_start_line_num = line_num
                        while sj.judge_line(module_lines[0]):
                            module_lines = module_lines[1:]
                            line_num += 1
                        module_lines[0] = convert_for_logic(module_lines[0], module_lines, module_name)
                        write_file.write(replace_in_line(module_lines[0]))
                        module_lines = module_lines[1:]
                write_file.write(line)

        except (StopIteration, Endmodule_exception):
            print('Error!! Irregular description around line ' + str(skip_start_line_num))

        read_file.close()
        write_file.close()

        make_signal_info(name_without_extension + '_conv.v', debug)
        expand_dot_asterisk(name_without_extension + '_conv.v', name_without_extension + '_eda.v')

        if os.path.exists(name_without_extension + '.v'):
            os.remove(name_without_extension + '.v')
        if (not debug) and (not is_testing):
            os.rename(name_without_extension + '_eda.v', name_without_extension + '.v')
            clean_directory()

    if is_testing:
        return module_data_base().module_dict, module_data_base().reg_dict, module_data_base().wire_dict

class Endmodule_exception(Exception): pass

def get_in_bracket_signals(line):
    in_bracket_signals = []
    words = line.replace(';', '').split(')')
    for word in words:
        in_bracket = word[word.rfind('(') + 1:].strip()
        if in_bracket:
            in_bracket_signals.append(word[word.rfind('(') + 1:].strip())
    return in_bracket_signals

def convert_for_logic(line, module_lines, module_name):
    logic_convert_dict = {'logic': 'reg', 'bit': 'reg', 'byte': 'reg [7:0]'}
    wire_convert_dict = {'logic': 'wire', 'bit': 'wire', 'byte': 'wire [7:0]'}
    wire_flag = False

    words = line.replace(';', '').split()
    if not words: return line
    if words[0] == 'input' or words[0] == 'output' or words[0] == 'inout':
        words = words[1:]
    if words[0] in logic_convert_dict.keys():
        if words[1][0] == '[':
            var_name = words[2]
        else:
            var_name = words[1]

        for i, templine in enumerate(module_lines):
            if 'assign' in templine and var_name in templine[0:templine.find('=')]:
                wire_flag = True
                break
            #elif var_name in module_data_base().module_dict[module_name].input:
            #    wire_flag = True
            #    break
            #elif var_name in module_data_base().module_dict[module_name].inout:
            #    wire_flag = True
            #    break
            elif get_mod_instance(templine):
                assigned_module = get_mod_instance(templine)
                dec_lines = []
                j = 0
                while ';' not in module_lines[i+j]:
                    dec_lines.append(module_lines[i+j])
                    j += 1
                dec_lines.append(module_lines[i+j])#add last line
                dec_line = ' '.join(dec_lines).replace('\n', ' ')
                if '*' in dec_line: #assigned by wild card or not
                    if var_name in module_data_base().module_dict[assigned_module].output:
                        wire_flag = True
                elif '.' in dec_line:
                    if var_name in get_in_bracket_signals(dec_line):
                        #assigned by port name
                        #  SUB sub(.CLK(CLK),.RST(RST),.IN(in1),.OUT1(OUT));
                        # .Port_name(Signal_name)
                        dec_line = util.clip_in_blacket(dec_line)
                        dec_line = dec_line.replace('.','')
                        assigned_ports = dec_line.split(',')
                        for comb in assigned_ports:
                            signal = util.clip_in_blacket(comb)
                            port = comb[0:comb.find('(')]
                            #print(port + ': ' +signal)
                            if signal == var_name:
                                if port in module_data_base().module_dict[assigned_module].output:
                                    wire_flag = True
                                    break
                        else:
                            raise Exception("Unexpected exception.")
                else: #assigned by order name
                    assigned_vars = util.clip_in_blacket(dec_line).split(',')
                    for i, assigned_var in enumerate(assigned_vars):
                        if assigned_var.strip() == var_name:
                            if module_data_base().module_dict[assigned_module].all_ports[i] == 'output':
                                wire_flag = True
                            break
##                    else:
##                        raise Exception("Unexpected exception.")

        if wire_flag:
            line = line.replace(words[0], wire_convert_dict[words[0]])
        else:
            line = line.replace(words[0], logic_convert_dict[words[0]])
    return line

class skip_judge(object):
    """ [CLASSES]
        For skip not verilog block.ec. property ~ endproperty, cloking ~ endclocking.
    """
    def __init__(self):
        self.default_flag = False
        self.assert_flag = False
        self.clocking_flag = False
        self.sequence_flag = False
        self.property_flag = False
##        self.end_word_dict = {'assert': ';',
##                              'default': ';',
##                              'clocking': 'endclocking',
##                              'sequence': 'endsequence',
##                              'property': 'endproperty'}

    def judge_line(self, line):
        if any([self.default_flag, self.assert_flag, self.clocking_flag,
                self.sequence_flag, self.property_flag]):
                    if 'endmodule' in line:
                        raise Endmodule_exception
        if self.assert_flag:
            self.assert_flag = ';' not in line
            return True
        elif self.default_flag:
            self.default_flag = ';' not in line
            return True
        elif self.clocking_flag:
            self.clocking_flag = 'endclocking' not in line
            return True
        elif self.sequence_flag:
            self.sequence_flag = 'endsequence' not in line
            return True
        elif self.property_flag:
            self.property_flag = 'endproperty' not in line
            return True
        else:
            if 'assert' in line:
                self.assert_flag = ';' not in line
                return True
            elif 'default' in line:
                self.default_flag = ';' not in line
                return True
            elif 'clocking' in line:
                self.clocking_flag = 'endclocking' not in line
                return True
            elif 'sequence' in line:
                self.sequence_flag = 'endsequence' not in line
                return True
            elif 'property' in line:
                self.property_flag = 'endproperty' not in line
                return True

def replace_in_line(line):
    def delete_word(word):
        targets = ('unique', 'priority')
        if word in targets:
            return ''
        else:
            return word

    def replace_word(word):
        replace_dict = {'always_comb': 'always @*', 'always_latch': 'always @*',
                        'always_ff': 'always','int': 'integer', 'shortint': 'reg signed [15:0]',
                        'longint': 'reg signed [63:0]', "'0": "'d0", "'1": "'hffff",
                        'parameter logic': 'parameter', "localparam logic": "localparam",
                        'function logic': 'function'}
        if word in replace_dict.keys():
            return replace_dict[word]
        else:
            return word

    words = line.split(' ')
    for i, word in enumerate(words):
        words[i] = delete_word(word)
        words[i] = replace_word(word)
    converted_line = ' '.join(words)
    return converted_line

def split_logic_decrarement(read_file_name, write_file_name):
    """ [Functions]
       input A;
       output B;
       logic A,B;
       ->
       input A;
       output B;
       logic A;
       logic B;
    """

    write_file = open(write_file_name, 'w')
    with open(read_file_name, 'r') as f:
        in_module = False
        dec_line = False
        for line in f:
            words = line.replace(',', '').split()
            if not words:
                write_file.write(line)
                continue
            if 'module' in line.split():
                new_module = module_info()
                dec_line = True
            if dec_line:
                write_file.write(line)
                if ';' in line:
                    dec_line = False
                    in_module = True
            elif set(['logic', 'bit', 'byte']).intersection(words) and ',' in line:
                decrarements, packed_bit, unpacked_bit, var_names = separate_in_bracket(line)
                for var in var_names:
                    write_file.write(' '.join(decrarements + unpacked_bit + (var,) + packed_bit) + ';\n')
            else:
                write_file.write(line)
    write_file.close()

def separate_in_bracket(line):
    """ [Functions]
         input logic [2: 1] A,B [1:0];
         ->
         declarements = ['input', 'logic']
         packed bit = '[2: 1]'
         var_names = ['A', 'B']
         unpacked_bit = '[1:0]'
    """
    decrarements = []
    packed_bit = []
    unpacked_bit = []
    var_names = []

    line = line.replace(',', ' ')
    line = line.replace(';', '')
    line = line.replace('[', ' [')
    line = line.replace(']', '] ')

    words = line.split()

    in_bracket_flag = False
    for word in words:
        if word in ('logic', 'bit', 'byte', 'input', 'output', 'inout'):
            decrarements.append(word)
        elif word[0] == '[':
            in_bracket_flag = (word[-1] != ']')
            if var_names:
                packed_bit.append(word)
            else:
                unpacked_bit.append(word)
        elif word[-1] == ']':
            in_bracket_flag = False
            if var_names:
                packed_bit.append(word)
            else:
                unpacked_bit.append(word)
        elif in_bracket_flag:
            if var_names:
                packed_bit.append(word)
            else:
                unpacked_bit.append(word)
        else:
            var_names.append(word)
    return (tuple(decrarements), tuple(packed_bit),
            tuple(unpacked_bit), tuple(var_names))

def delete_comments(read_file_name, write_file_name):
    """ [Functions]
       delete char after '//' and from '/*' to '*/'
    """
    write_file = open(write_file_name, 'w')
    with open(read_file_name, 'r') as f:
        block_comment_flag = False
        for line in f:
            if block_comment_flag:
                if line.find('*/'):
                    write_file.write(line[line.find('*/'):-1])
                else:
                    continue
            elif line.find('//') >= 0:
                write_file.write(line[0:line.find('//')])
            elif line.find('/*') >= 0:
                if line.find('*/'):
                    write_file.write(line[0:line.find('/*')] + line[line.find('*/'):-1])
                else:
                    write_file.write(line[0:line.find('/*')])
                    block_comment_flag = True
            else:
                write_file.write(line)
    write_file.close()

def expand_enum(read_file_name, write_file_name):
    def get_enum_values(line):
        line = util.clip_in_blacket(line, '{')
        line = line.replace(' ','')
        line = line.replace('\t','')

        enum_dict = OrderedDict()
        i = 0
        for val in line.split(','):
            if '=' in val:

                i = int(val[val.find('=') + 1:])

                enum_dict[val[0:val.find('=')]] = i
            else:
                enum_dict[val] = i
            i += 1
        return enum_dict
    write_file = open(write_file_name, 'w')
    with open(read_file_name, 'r') as f:
        for line in f:
            if 'enum' in line.split():
                for val, num in get_enum_values(line).items():
                    write_file.write(" ".join(('localparam', val, "= 'd", str(num), ';')))
            else:
                write_file.write(line)
    write_file.close()

def make_module_info(read_file_name, debug=False):
    with open(read_file_name, 'r') as f:
        in_module = False
        dec_line = False
        for line in f:
            if 'module' in line.split():
                new_module = module_info()
                dec_line = True
            if dec_line:
                new_module.dec_lines.append(line)
                if ';' in line:
                    dec_line = False
                    new_module.readfirstline()
                    in_module = True
            elif re.match('endmodule', line):
                in_module = False
                mdb = module_data_base()
                mdb.set_module(new_module.name, new_module)
                if debug:
                    print(new_module.tostr())
            elif in_module:
                new_module.readline(line)

def make_signal_info(read_file_name, debug):
    with open(read_file_name, 'r') as f:
        in_module = False
        dec_line = False
        for line in f:
            if 'module' in line.split():
                new_module = module_signal_info()
                dec_line = True
            if dec_line:
                new_module.dec_lines.append(line)
                if ';' in line:
                    dec_line = False
                    new_module.readfirstline()
                    in_module = True
            elif re.match('endmodule', line):
                in_module = False
                mdb = module_data_base()
                mdb.set_signal_dict(new_module.name, new_module)
                if debug:
                    print(new_module.tostr())
            elif in_module:
                new_module.readline(line)

def expand_dot_asterisk(read_file_name, write_file_name):
    """ [Functions]
       OUT(.*) -> OUT(.SIG1(SIG1),.SIG2(SIG2))
    """
    write_file = open(write_file_name, 'w')
    with open(read_file_name, 'r') as f:
        in_module = False
        dec_line = False
        for line in f:
            if 'module' in line.split():
                this_module = get_module_name_from_decline(line)
                in_module = True
            elif re.match('endmodule', line):
                in_module = False
            elif in_module:
                if '.*' in line:
                    #TODO after implemented get_signals
                    assined_module = get_module_name_from_insline(line)
                    assined_module_info = module_data_base().module_dict[assined_module]
                    ports = assined_module_info.input + assined_module_info.inout + assined_module_info.output
                    signals = module_data_base().reg_dict[this_module] + module_data_base().wire_dict[this_module]
                    decs = set(ports) & set(signals)
                    dec_replace = ', '.join(['.' +dec + '(' + dec + ')' for dec in decs])
                    line = line.replace('.*', dec_replace)
            write_file.write(line)
    write_file.close()

def convert_logic_in_fl(first_line):
    first_line = re.sub('input +logic +', 'input wire ', first_line)
    first_line = re.sub('inout +logic +', 'input wire ', first_line)
    first_line = re.sub('output +logic +', 'output wire ', first_line)

    return first_line

def get_mod_instance(line):
    words = set(line.replace('(', ' ').split())
    if words.intersection(module_data_base().module_dict.keys()):
        return tuple(words.intersection(module_data_base().module_dict.keys()))[0]
    else:
        return None

def clean_directory():
    for (root, dirs, files) in os.walk(u'.'):
        for file in files:
            if '_comdel.v' in file:
                os.remove(u'./' + file)
            elif '_eexpand.v' in file:
                os.remove(u'./' + file)
            elif '_split.v' in file:
                os.remove(u'./' + file)
            elif '_eda.v' in file:
                os.remove(u'./' + file)

class module_data_base(object):
    """ [CLASSES]
        Singleton class for manage terminals for module data base.
    """
    _singleton = None
    def __new__(cls, *argc, **argv):
        if cls._singleton is None:
            cls._singleton = object.__new__(cls)
            cls.module_dict = {}
            cls.reg_dict = {}
            cls.wire_dict = {}
        return cls._singleton

    def set_module(self, module_name, module_info):
        assert not module_name in self.module_dict.keys()
        self.module_dict[module_name] = module_info

    def set_signal_dict(self, module_name, signal_info):
        self.wire_dict[module_name] = signal_info.wire
        self.reg_dict[module_name] = signal_info.reg

    def flash(self):
        self.module_dict = {}
        self._singleton = None

class module_info(object):
    def __init__(self):
        self.name = ''
        self.dec_lines = []
        self.input = []
        self.output = []
        self.inout = []
        self.all_ports = []

    def _add_port(self, port_name, port_type):
        if port_type == 'input':
            self.input.append(port_name)
        elif port_type == 'inout':
            self.inout.append(port_name)
        elif port_type == 'output':
            self.output.append(port_name)
        self.all_ports.append(port_type)

    def readfirstline(self):
        """[FUNCTIONS]
        ex.
        module COMPARE(output GT, output LE, output EQ,
                       input [1:0] A, input [1:0] B, input C);
        """
        first_line = " ".join(self.dec_lines)
        first_line = first_line.replace('\n', ' ')
        self.name = get_module_name_from_decline(first_line)

        if ('input' not in first_line and 'inout' not in first_line
            and 'output' not in first_line):
                return
        first_line = re.sub("#\(.+?\)", " ", first_line)
        first_line = re.sub("\[.+?\]", " ", first_line)
        in_bracket = util.clip_in_blacket(first_line)
        decs = in_bracket.split(',')
        #words[-1] :exclude type definition
        for dec in decs:
            words = dec.split()
            self._add_port(words[-1], words[0])

    def readline(self, line):
        """[FUNCTIONS]
        ex.
        module COMPARE(GT, LE, EQ, A, B, C);
            output GT, LE, EQ;
            input [1: width_A] A, B;
            input [1: width_B] C;
        """
        #line = line.replace('(', ' ')
        #line = line.replace(')', ' ')
        line = re.sub("\[.+?\]", " ", line)
        line = line.replace(';', ' ;')
        line = line.replace(',', ' ')
        in_input_port = False
        in_output_port = False
        in_inout_port = False
        for word in line.split():
            if word == 'input':
                assert(not(in_input_port) and not(in_output_port) and not(in_inout_port))
                in_input_port = True
            elif word == 'output':
                assert(not(in_input_port) and not(in_output_port) and not(in_inout_port))
                in_output_port = True
            elif word == 'inout':
                assert(not(in_input_port) and not(in_output_port) and not(in_inout_port))
                in_inout_port = True
            elif word == ';':
                in_input_port = False
                in_output_port = False
                in_inout_port = False
            elif in_input_port:
                self._add_port(word, 'input')
            elif in_output_port:
                self._add_port(word, 'output')
            elif in_inout_port:
                self._add_port(word, 'inout')

    def tostr(self):
        return self.name + '\ninput:' + str(self.input) + '\noutput:' + str(self.output) + '\ninout:'+ str(self.inout)


class module_signal_info(object):
    def __init__(self):
        self.name = ''
        self.dec_lines = []
        self.reg = []
        self.wire = []

    def _add_signal(self, signal_names, signal_type):
        if signal_type == 'reg':
            self.reg += signal_names
        elif signal_type == 'wire':
            self.wire += signal_names

    def readfirstline(self):
        """[FUNCTIONS]
        ex.
        module COMPARE(output GT, output LE, output EQ,
                       input [1:0] A, input [1:0] B, input C);
        """
        first_line = " ".join(self.dec_lines)
        first_line = first_line.replace('\n', ' ')
        self.name = get_module_name_from_decline(first_line)

    def readline(self, line):
        """[FUNCTIONS]
        ex.
        module COMPARE(GT, LE, EQ, A, B, C);
            output GT, LE, EQ;
            input [1: width_A] A, B;
            input [1: width_B] C;
        """
        #line = line.replace('(', ' ')
        #line = line.replace(')', ' ')
        line = re.sub("\[.+?\]", " ", line)
        line = line.replace(';', '')
        line = line.replace(',', ' ')
        for i, word in enumerate(line.split()):
            if word == 'reg' or word == 'wire':
                self._add_signal(line.split()[i + 1:], word)

    def tostr(self):
        return self.name + '\nreg:' + str(self.reg) + '\nwire:' + str(self.wire)

def get_module_name_from_decline(line):
    line = re.sub("#\(.+?\)", " ", line) #remove parameter description
    return line.replace('(', ' ').split()[1]

def get_module_name_from_insline(line):
    line = re.sub("#\(.+?\)", " ", line) #remove parameter description
    return line.replace('(', ' ').split()[0]

if __name__ == '__main__':
    convert2sv(["../test/dot_asterisk.sv",])
    #convert2sv(["../test/name_and_order_assign.sv",])
