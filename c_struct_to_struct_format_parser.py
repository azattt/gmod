import pycparser
import pycparser.c_ast

FORMATS = {
    "char": "c",
    "signed char": "b",
    "unsigned char": "B",
    "bool": "?",
    "short": "h",
    "unsigned short": "H",
    "int": "i",
    "unsigned int": "I",
    "long": "l",
    "unsigned long": "L",
    "long long": "q",
    "unsigned long long": "Q",
    "ssize_t": "n",
    "size_t": "N",
    "float": "f",
    "double": "d",
    "void*": "P",
}


def parse(c_code: str, unused_is_pad_byte: bool = True) -> tuple[dict, dict, dict]:
    parser = pycparser.CParser()
    parsed = parser.parse(c_code)
    formats = FORMATS
    var_names = {}
    multis = {}
    for i in parsed:
        if isinstance(i, pycparser.c_ast.Typedef):
            if isinstance(i.type, pycparser.c_ast.TypeDecl):
                if isinstance(i.type.type, pycparser.c_ast.IdentifierType):
                    formats[i.type.declname] = formats[" ".join(i.type.type.names)]
                elif isinstance(i.type.type, pycparser.c_ast.Struct):
                    struct_format = ""
                    var_name = []
                    for j in i.type.type:
                        if isinstance(j, pycparser.c_ast.Decl):
                            if isinstance(j.type, pycparser.c_ast.TypeDecl):
                                struct_format += "".join(
                                    formats[" ".join(j.type.type.names)]
                                )
                                var_name.append(j.type.declname)
                            else:
                                raise RuntimeError(j)
                        else:
                            raise RuntimeError(j)
                        
                    formats[i.type.declname] = struct_format
                    var_names[i.type.declname] = var_name
                else:
                    raise RuntimeError(i)
            else:
                raise RuntimeError(i)
        elif isinstance(i, pycparser.c_ast.Decl):
            if isinstance(i.type, pycparser.c_ast.Struct):
                struct_format = ""
                var_name = []
                multi = []
                for j in i.type:
                    if isinstance(j, pycparser.c_ast.Decl):
                        if isinstance(j.type, pycparser.c_ast.TypeDecl):
                            if j.name.find("unused") != -1 and unused_is_pad_byte:
                                struct_format += "x"
                            else:
                                struct_format += "".join(
                                    formats[" ".join(j.type.type.names)]
                                )
                                if len(formats[" ".join(j.type.type.names)]) == 1:
                                    var_name.append(j.type.declname)
                                else:
                                    multi.append((j.type.declname, len(formats[" ".join(j.type.type.names)])))
                                    for k in range(len(formats[" ".join(j.type.type.names)])):
                                        var_name.append(j.type.declname+str(k))
                        elif isinstance(j.type, pycparser.c_ast.ArrayDecl):
                            struct_format += j.type.dim.value
                            if isinstance(j.type.type, pycparser.c_ast.TypeDecl):
                                if j.name.find("unused") != -1 and unused_is_pad_byte:
                                    struct_format += "x"
                                else:
                                    if " ".join(j.type.type.type.names) == 'char':
                                        struct_format += "s"
                                        var_name.append(j.type.type.declname)
                                    else:
                                        struct_format += "".join(
                                            formats[" ".join(j.type.type.type.names)]
                                        )
                                        if len(formats[" ".join(j.type.type.type.names)]) == 1:
                                            var_name.append(j.type.type.declname)
                                        else:
                                            multi.append((j.type.type.declname, len(formats[" ".join(j.type.type.type.names)])))
                                            for k in range(len(formats[" ".join(j.type.type.type.names)])):
                                                var_name.append(j.type.type.declname+str(k))
                        else:
                            raise RuntimeError(j)
                    else:
                        raise RuntimeError(j)
                formats[i.type.name] = struct_format
                var_names[i.type.name] = var_name
                multis[i.type.name] = multi
            else:
                raise RuntimeError(i)
        else:
            raise RuntimeError(i)
    return (formats, var_names, multis)


def to_python_code(parsed: tuple[dict, dict, dict], struct_name: str) -> str:
    for struct_name in parsed[1].keys():
        python_code = f'{struct_name}_format = "{parsed[0][struct_name]}"\n'
        python_code += f'{struct_name}_size = struct.calcsize({struct_name}_format)\n'
        for i in parsed[1][struct_name]:
            python_code += i
            if i != parsed[1][struct_name][-1]:
                python_code += ', '
        python_code += f" = struct.unpack({struct_name}_format, {struct_name}_data[:{struct_name}_size])\n"
        for multi in parsed[2][struct_name]:
            python_code += f"{multi[0]} = ("
            for k in range(multi[1]):
                python_code += multi[0] + str(k)
                if k != multi[1] - 1:
                    python_code += ", "
            python_code += ')\n'

        return python_code


def main():
    with open("preprocessed.c", encoding="utf8") as file:
        data = file.read()

    print(to_python_code(parse(data), "studiohdr2_t"))


if __name__ == "__main__":
    main()
