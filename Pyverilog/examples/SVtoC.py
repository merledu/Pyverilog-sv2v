import re
import os
import math

filenames_sv = ['test_code.sv']
func_all = {}
func_all[""] = {}


def const_sub(current_line):
    current_line = re.sub(r"`(?=[A-Z])", "", current_line)
    current_line = re.sub(r"\d*'b", "0b", current_line)
    current_line = re.sub(r"\d*'d", "", current_line)
    current_line = re.sub(r"\d*'h", "0x", current_line)
    current_line = re.sub(r"'", "", current_line)
    current_line = re.sub(r"\r\n", "\n", current_line)
    current_line = re.sub(r"\$urandom_range", "urandom_range", current_line)
    if re.findall(r"urandom_range", current_line):
        if not re.findall(r"urandom_range\s*\(\s*\d+\s*,", current_line):
            current_line = re.sub(r"urandom_range\s*\(", "urandom_range(0,", current_line)
    datab = re.findall("0b\w+", current_line)
    for i in datab:
        if re.search("_", i):
            i_new = re.sub("_", "", i)
            current_line = re.sub(i, i_new, current_line)
    datah = re.findall("0x\w+", current_line)
    for i in datah:
        if re.search("_", i):
            i_new = re.sub("_", "", i)
            current_line = re.sub(i, i_new, current_line)
    return current_line


def keyword_sub(current_line):
    current_line = re.sub(r"`ifdef", "#ifdef", current_line)
    current_line = re.sub(r"`ifndef", "#ifndef", current_line)
    current_line = re.sub(r"`define", "#define", current_line)
    current_line = re.sub(r"`endif", "#endif", current_line)
    current_line = re.sub(r"\bbegin\b", "\n{", current_line)
    current_line = re.sub(r"\bend\b", "}\n", current_line)
    current_line = re.sub("null", "NULL", current_line)
    return current_line


def function_param_sub(current_line, init_param_dict):
    current_line = re.sub(r"\.", "_", current_line)
    current_line = re.sub(r"\s*(task|function).*::", "void ", current_line)
    current_line = re.sub(r"input(\s+(bit|integer))? ", "uint32_t ", current_line)
    current_line = re.sub(r"int ", "uint32_t ", current_line)
    current_line = re.sub(r"output\s+string ", "char *", current_line)
    current_line = re.sub(r"output(\s+bit)? ", "uint32_t *", current_line)
    current_line = re.sub(r"string ", "char *", current_line)
    bit_widths = re.findall(r"\s*\[\d+:\d+\]\s*", current_line)
    for width in bit_widths:
        temp = width.strip()[1:-1].split(":")
        temp = list(map(int, temp))
        width = re.sub(r"\[", "\\[", width)
        width = re.sub(r"\]", "\\]", width)
        if temp[0] <= 31 and temp[1] <= 31:
            current_line = re.sub(width, " ", current_line)
        else:
            current_line = re.sub(width, " *", current_line)
            current_line = re.sub(r"\* \*", "*", current_line)
    init_param_names = re.findall(r"\b\w+\b\s*(?==)", current_line)
    init_param_values = re.findall(r"(?<==)\s*\"*\w*\"*", current_line)
    # if len(init_param_names) != len(init_param_values):
    #    print current_line
    for i in range(len(init_param_names)):
        current_line = re.sub(r"(?<==)" + init_param_values[i], "", current_line)
        init_param_dict[init_param_names[i]] = init_param_values[i]
    current_line = re.sub("=", "", current_line)
    return current_line


def local_variable_sub(current_line):
    current_line = re.sub(r"\s*(bit|reg|logic|integer)\s*", "uint32_t ", current_line)
    # current_line = re.sub(r"\s*reg\s*", "uint32_t ", current_line)
    if not re.search("=", current_line):
        current_line = re.sub(r";", "=0;", current_line)
    bit_widths = re.findall(r"\[\d+:\d+\]\s*", current_line)
    for width in bit_widths:
        temp = width.strip()[1:-1].split(":")
        temp = list(map(int, temp))
        width = re.sub(r"\[", "\\[", width)
        width = re.sub(r"\]", "\\]", width)
        current_line = re.sub(width, "", current_line)
        if temp[0] > 31 or temp[1] > 31:
            array_size = max(temp[0], temp[1])
            array_size = str(int(math.ceil(array_size / 32.0)))
            if re.search("=0;", current_line):
                array_size = "[" + array_size + "]" + "={0};"
                current_line = re.sub(r"=0;", array_size, current_line)
            else:
                array_size = "[" + array_size + "]"
                current_line = re.sub(r"=", array_size + "=", current_line)
                current_line = re.sub(r";", ";//!!!the value may need to revise", current_line)

    return current_line


def local_string_sub(current_line):
    current_line = re.sub(r"\s*string\s*", "char ", current_line)
    current_line = re.sub(r"\s*;", "[MAX_STRING_LENGTH]={0};", current_line)
    return current_line


def printf_sub(current_line):
    current_line = re.sub(r"\{", "", current_line)
    current_line = re.sub(r"\}", "", current_line)
    current_line = re.sub(r"`uvm_.+?(?=\")", "    DDR_PRINT(", current_line)
    current_line = re.sub(r"\$display", "    DDR_PRINT", current_line)
    current_line = re.sub(r"%\d*t", "", current_line)
    current_line = re.sub(r"(?<=\))(,\s*UVM_[A-Z]+\s*)*\);?", ";", current_line)
    current_line = re.sub(r",\s*\$time\s*", "", current_line)
    if re.search(r"ERROR", current_line):
        current_line = re.sub("DDR_PRINT", "DDR_ERROR", current_line)
    current_line = re.sub(r"\"\s*(?=,|\))", r'\\n"', current_line)
    return current_line


def bits_set_sub(current_line):
    bit_widths = re.findall(r"(?<=\[)\s*\d+\s*(?=\])", current_line)
    for width in bit_widths:
        current_line = re.sub(r"(?<=\[)" + width + r"(?=\])", width + ":" + width, current_line)
    var = current_line.split("=")
    var[1] = var[1].strip()
    var[0] = var[0].strip()
    var1_widths = re.findall(r"\w+\s*\[.*?\]", var[1])
    var0_widths = re.findall(r"\w+\s*\[.*?\]", var[0])
    if var1_widths:
        width = var1_widths[0]
        width = "GET_BITS_VAL(" + width.strip()
        width = re.sub(r":", ',', width)
        width = re.sub(r"\[", ',', width)
        width = re.sub(r"\]", ');', width)
        var[1] = width + "\n"
        return var[0] + "=" + var[1]
    elif var0_widths:
        width = var0_widths[0]
        width = "SET_BITS_VAL(" + width.strip()
        width = re.sub(r":", ',', width)
        width = re.sub(r"\[", ',', width)
        width = re.sub(r"\]", ',', width)
        width = width + var[1]
        width = re.sub(r";", ');', width)
        return width + "\n"
    else:
        return current_line


def bits_get_sub(current_line):
    bit_widths = re.findall(r"(?<=\[)\s*\d+\s*(?=\])", current_line)
    for width in bit_widths:
        current_line = re.sub(r"(?<=\[)" + width + r"(?=\])", width + ":" + width, current_line)
    var = re.split("!=|==", current_line)
    var[0] = var[0].strip()
    var[1] = var[1].strip()
    var1_widths = re.findall(r"\w+\s*\[.*?\]", var[1])
    var0_widths = re.findall(r"\w+\s*\[.*?\]", var[0])
    if var1_widths:
        width = var1_widths[0]
        var1_widths = re.sub(r"\[", "\\[", var1_widths[0])
        var1_widths = re.sub(r"\]", "\\]", var1_widths)
        width = "GET_BITS_VAL(" + width
        width = re.sub(r":", ',', width)
        width = re.sub(r"\[", ',', width)
        width = re.sub(r"\]", ')', width)
        current_line = re.sub(var1_widths, width, current_line)
    if var0_widths:
        width = var0_widths[0]
        var0_widths = re.sub(r"\[", "\\[", var0_widths[0])
        var0_widths = re.sub(r"\]", "\\]", var0_widths)
        width = "GET_BITS_VAL(" + width
        width = re.sub(r":", ',', width)
        width = re.sub(r"\[", ',', width)
        width = re.sub(r"\]", ')', width)
        current_line = re.sub(var0_widths, width, current_line)
    return current_line


def string_set_sub(current_line):
    string_var = re.findall(r"\b\w+\b(?=\s*=\s*\")", current_line)
    if string_var:
        string_var = string_var[0]
        current_line = re.sub(string_var, "strcpy(" + string_var, current_line)
        current_line = re.sub(r"=", ",", current_line)
        current_line = re.sub(r"\"\s*;", "\");", current_line)
    return current_line


def transfer_sv_2_c_temp(sv_file_name):
    global func_all
    func_current = {}
    func_current[""] = {}

    c_file_name = re.sub(r"\.sv", ".temp", sv_file_name)
    h_file_name = re.sub(r"\.sv", ".h", sv_file_name)
    just_file_name = re.findall(r"\w+(?=\.sv)", sv_file_name)[0]

    flag_in_case = 0
    current_func_name = ""
    current_func_param = []
    fr = open(sv_file_name, 'r')
    fw = open(c_file_name, 'w')
    fwh = open(h_file_name, 'w')

    count_folder = sv_file_name.count("/") - 1
    public_h = ""
    for i in range(count_folder):
        public_h += "./"
    public_h += "hbm_public"
    fw.write("#include \"" + public_h + ".h\"\n")
    fw.write("#include \"" + just_file_name + ".h\"\n")

    fwh.write("#ifndef __" + just_file_name.upper() + "_H\n")
    fwh.write("#define __" + just_file_name.upper() + "_H\n\n")

    while True:
        current_line = fr.readline()

        if not current_line:
            break

        if current_line.strip().startswith("//"):
            fw.write(current_line)
            continue

        if current_line.strip().startswith("/*"):
            fw.write(current_line)
            continue

        if current_line.strip().endswith("*/"):
            fw.write(current_line)
            continue

        if re.match(r"\s*\bclass\b", current_line):
            fw.write("/*\n" + current_line)
            while not re.match(r"\s*\bendclass\b", current_line):
                current_line = fr.readline()
                fw.write(current_line)
            fw.write("*/\n")
            continue

        if re.match(r"\s*\b(task|function)\b", current_line):
            init_param_dict = {}
            if re.search(r"//", current_line):
                current_line = current_line.split("//")[0]
            current_line = const_sub(current_line)
            declaration = current_line.strip()
            while not re.search(";", current_line):
                current_line = fr.readline()
                if re.search(r"//", current_line):
                    current_line = current_line.split("//")[0]
                current_line = const_sub(current_line)
                declaration = declaration + current_line.strip()
            current_line = declaration
            func_name = re.findall(r"\b\w+\b\s*(?=\()", current_line)
            if func_name:
                func_name = func_name[0].strip()
                func_current[func_name] = {}
                current_func_name = func_name
            current_line = function_param_sub(current_line, init_param_dict)
            params = re.findall(r"(?<=\().+(?=\))", current_line)
            fwh.write(current_line + "\n")
            if params:
                params = params[0].split(",")
                for index, item in enumerate(params):
                    param_name = item.strip().split(" ")[-1]
                    param_name = re.sub(r"\*", "", param_name).strip()
                    if re.search(r"uint32_t\s*\*", item):
                        func_current[func_name][param_name] = index
            if func_name:
                if func_current[func_name] == {}:
                    func_current.pop(func_name)
            current_line = re.sub(r";", "\n{\n", current_line)
            fw.write(current_line)
            for assign in init_param_dict.items():
                current_line = assign[0] + "=" + assign[1] + ";\n"
                current_line = string_set_sub(current_line)
                fw.write("//" + current_line)
            fw.write("FUNC_PRINT(\"enter " + current_func_name + "()\\n\");\n")
            continue

        if re.match(r"\s*\b(endtask|endfunction)\b", current_line):
            fw.write("FUNC_PRINT(\"exit " + current_func_name + "()\\n\");\n")
            fw.write("}\n")
            current_func_name = ""
            current_func_param = []
            continue

        if re.match(r"\s*\bvirtual\b", current_line):
            if re.search(r"\s*virtual\s*task\s*body", current_line):
                fw.write("void " + just_file_name + "()\n{\n")
            else:
                fw.write(current_line)
            continue

        if re.search(r"//", current_line):
            comment = current_line.split("//")[1]
            fw.write("//" + comment)
            current_line = current_line.split("//")[0] + "\n"

        if re.match(r"\s*(`uvm_|\$display)", current_line):
            current_line = printf_sub(current_line)
            current_line = re.sub(r"%h", "0x%x", current_line)
            fw.write(current_line)
            continue

        current_line = const_sub(current_line)

        if re.match(r"\s*\brepeat\b", current_line):
            repeat_time = re.findall(r"(?<=\().+(?=\))", current_line)
            current_line = re.findall(r"(?<=\)).+", current_line)[0] + "\n"
            if repeat_time:
                repeat_time = repeat_time[0]
                fw.write("for(int i = 0;i < " + repeat_time + ";i ++)\n")

        if re.match(r"\s*#\s*\d+", current_line):
            if re.search(r"us", current_line):
                data = re.findall(r"\d+", current_line)[0]
            elif re.search(r"ns", current_line):
                data = re.findall(r"\d+", current_line)[0]
                data = int(data) / 1000
                if data == 0:
                    data = 1
                data = str(data)
            else:
                data = "1"
            current_line = "usleep(" + data + "); //" + current_line
            fw.write(current_line)
            continue

        if re.match(r"\s*\b(reg|bit|logic|integer)\b", current_line):
            current_line = local_variable_sub(current_line)
            fw.write(current_line)
            if re.search("={0}", current_line):
                param_temp = re.findall(r"(?<=uint32_t)\s*\w+\s*(?=\[)", current_line)
                for i in param_temp:
                    current_func_param.append(i.strip())
            continue

        if re.match(r"\s*\bstring\b", current_line):
            current_line = local_string_sub(current_line)
            fw.write(current_line)
            continue

        if re.match(r"\s*\bcase\b", current_line):
            current_line = re.sub("case", "switch", current_line)
            current_line = keyword_sub(current_line)
            fw.write(current_line)
            fw.write("{\n")
            flag_in_case = 1
            continue

        if re.match(r"\s*\bendcase\b", current_line):
            fw.write("}\n")
            flag_in_case = 0
            continue

        if flag_in_case == 1:
            current_line = current_line.strip()
            if not current_line.strip().startswith("default"):
                fw.write("case(")
                current_line = re.sub(r"\s*:", "):", current_line, 1)
            current_line = re.sub(";", ";break;\n", current_line)

        if re.search(r"(?<!(!|=))=(?!=)", current_line):
            current_line = bits_set_sub(current_line)
            if re.search(r"_VAL\(", current_line):
                param_vals = re.findall(r"(?<=_VAL\()\w+(?=,)", current_line)
                for val in param_vals:
                    if val in current_func_param:
                        current_line = re.sub("BITS", "ARRAY", current_line)
                    if current_func_name in func_current:
                        if val in func_current[current_func_name].keys():
                            current_line = re.sub("BITS", "ARRAY", current_line)
                current_line = keyword_sub(current_line)
                fw.write(current_line)
                continue

        if re.search(r"==|!=", current_line):
            current_line = bits_get_sub(current_line)
            if re.search(r"_VAL\(", current_line):
                param_vals = re.findall(r"(?<=_VAL\()\w+(?=,)", current_line)
                for val in param_vals:
                    if val in current_func_param:
                        current_line = re.sub("BITS", "ARRAY", current_line)
                    if current_func_name in func_current:
                        if val in func_current[current_func_name].keys():
                            current_line = re.sub("BITS", "ARRAY", current_line)
                current_line = keyword_sub(current_line)
                fw.write(current_line)
                continue

        if re.search(r"=\s*\"", current_line):
            current_line = string_set_sub(current_line)
            current_line = keyword_sub(current_line)
            fw.write(current_line)
            continue

        if current_func_name:
            params = re.findall(r"\b\w+\b", current_line)
            for i in params:
                if i in current_func_param:
                    current_line = re.sub(r"\b" + i + r"\b", "(*" + i + ")", current_line)
                if current_func_name in func_current:
                    if i in func_current[current_func_name].keys():
                        current_line = re.sub(r"\b" + i + r"\b", "(*" + i + ")", current_line)
                # if i in func_current.keys():
                #    if func_current[i] != {}:
                #        for j in func_current[i].keys():
                #            temp = func_current[i][j]
                #            func_call_param = re.findall(r"(?<=\().+(?=\))",current_line)
                #            for k in func_call_param:
                #                k = k.split(",")
                #                current_line = re.sub(r"\b"+k[temp].strip()+r"\b","(&" + k[temp].strip() + ")",current_line)
            # current_line = re.sub(r"\*\(\&|\&\(\*","(",current_line)
            current_line = re.sub(r"\*\(\*", "*(", current_line)

        current_line = keyword_sub(current_line)
        fw.write(current_line)

    func_all.update(func_current)
    fwh.write("\n#endif\n")

    fr.close()
    fw.close()
    fwh.close()


def transfer_c_temp_2_c(ctemp_file_name):
    global func_all

    ctemp_file_name = re.sub(r"\.sv", ".temp", ctemp_file_name)
    c_file_name = re.sub(r"\.temp", ".c", ctemp_file_name)
    fr = open(ctemp_file_name, 'r')
    fw = open(c_file_name, 'w')

    while True:
        current_line = fr.readline()

        if not current_line:
            break

        if current_line.strip().startswith("//"):
            fw.write(current_line)
            continue

        if re.findall(r"/\*", current_line):
            while not re.findall(r"\*/", current_line):
                fw.write(current_line)
                current_line = fr.readline()
            fw.write(current_line)
            continue

        if re.match("void", current_line):
            fw.write(current_line)
            continue

        if re.findall("_PRINT", current_line):
            fw.write(current_line)
            continue

        params = re.findall(r"\b\w+\b", current_line)
        # flag_comment = 0
        # saved_comment = ""
        for i in params:
            if i in func_all.keys():
                if func_all[i] != {}:
                    for j in func_all[i].keys():
                        temp = func_all[i][j]
                        func_call_param = re.findall(r"(?<=\().+(?=\))", current_line)
                        for k in func_call_param:
                            k = k.split(",")
                            for index, each_param in enumerate(k):
                                pure_param = re.findall(r"(?<=\(\*)\w+(?=\))", each_param)
                                if pure_param:
                                    k[index] = pure_param[0]
                                    each_param = pure_param[0]
                                # each_param = each_param.split("[")
                                # if len(each_param) > 1:
                                #    flag_comment = 1
                                #    if not saved_comment:
                                #        saved_comment = current_line
                                #    k[index] = each_param[0]
                            current_line = re.sub(r"\b" + k[temp].strip() + r"\b", r"(&" + k[temp].strip() + r")",
                                                  current_line)
        current_line = re.sub(r"\*\(\&|\&\(\*", "(", current_line)
        # if flag_comment == 1:
        #    fw.write("//!!!attention " + saved_comment)
        fw.write(current_line)

    fr.close()
    fw.close()
    #os.system("rm " + ctemp_file_name)


def get_file(path):
    global filenames_sv
    filelisttemp = os.listdir(path)
    for filename in filelisttemp:
        if os.path.isdir(path + "/" + filename):
            get_file(path + "/" + filename)
        elif filename.endswith(".sv"):
            filenames_sv.append(path + "/" + filename)


get_file('.')
for fn in filenames_sv:
    transfer_sv_2_c_temp(fn)
for fn in filenames_sv:
    transfer_c_temp_2_c(fn)

# print filenames_sv
# transfer_sv_2_c("phy_init_seq.sv")
# transfer_sv_2_c("sub_tests/hbm_1500_aerr_test.sv")

# print func_all
