"""
Converts .c file of structs to ctypes.Structure
You can use #pragma CTYPES_PACK n in input .c file to define ctypes.Structure._pack_ parameter
"""
import warnings

import pycparser
import pycparser.c_ast

CTYPES_NAMES = {
    "char": "ctypes.c_char",
    "signed char": "ctypes.c_byte",
    "unsigned char": "ctypes.c_ubyte",
    "bool": "ctypes.c_bool",
    "short": "ctypes.c_short",
    "unsigned short": "ctypes.c_ushort",
    "int": "ctypes.c_int",
    "unsigned int": "ctypes.c_uint",
    "long": "ctypes.c_long",
    "unsigned long": "ctypes.c_ulong",
    "long long": "ctypes.c_longlong",
    "unsigned long long": "ctypes.c_ulonglong",
    "ssize_t": "ctypes.c_size_t",
    "size_t": "ctypes.c_ssize_t",
    "float": "ctypes.c_float",
    "double": "ctypes.c_double",
    "void*": "ctypes.c_int", # because mdl uses 4 bytes
}


def to_ctypes_struct(struct_name: str, struct_node: pycparser.c_ast.Struct, ctypes_pack: int) -> str:
    fields: list[str] = []
    for j in struct_node:
        if isinstance(j, pycparser.c_ast.Decl):
            if isinstance(j.type, pycparser.c_ast.TypeDecl):
                c_name = " ".join(j.type.type.names)
                fields.append(f'("{j.type.declname}", {CTYPES_NAMES.get(c_name, c_name)})')
            elif isinstance(j.type, pycparser.c_ast.PtrDecl):
                c_name = " ".join(j.type.type.type.names) + "*"
                warnings.warn(f"Pointer discarded: {c_name}")
                c_name = "void*"
                fields.append(f'("{j.type.type.declname}", {CTYPES_NAMES.get(c_name, c_name)})')
            elif isinstance(j.type, pycparser.c_ast.ArrayDecl):
                c_name = " ".join(j.type.type.type.names)
                fields.append(f'("{j.type.type.declname}", {CTYPES_NAMES.get(c_name, c_name)} * {j.type.dim.value})')
            else:
                raise RuntimeError(j)
        else:
            raise RuntimeError(j)

    struct_code = f"class {struct_name}(PrintableStruct):\n"
    struct_code += " " * 4 + "_fields_ = (\n"
    for field in fields:
        struct_code += " " * 8 + field + ",\n"
    struct_code += " " * 4 + ")\n"

    if ctypes_pack:
        struct_code += " " * 4 + "_pack_ = " + str(ctypes_pack)
    return struct_code


def get_decls(c_code: str) -> dict[str, str]:
    parser = pycparser.CParser()
    parsed = parser.parse(c_code)
    decls: dict[str, str] = {}
    ctypes_pack = 0
    for node in parsed:
        if isinstance(node, pycparser.c_ast.Typedef):
            if isinstance(node.type, pycparser.c_ast.TypeDecl):
                if isinstance(node.type.type, pycparser.c_ast.IdentifierType):
                    decls[node.type.declname] = f"{node.type.declname} = " + CTYPES_NAMES.get(" ".join(node.type.type.names), " ".join(node.type.type.names))
                elif isinstance(node.type.type, pycparser.c_ast.Struct):
                    decls[node.type.declname] = to_ctypes_struct(node.name, node.type.type, ctypes_pack)
                else:
                    raise RuntimeError(node)
            else:
                raise RuntimeError(node)
        elif isinstance(node, pycparser.c_ast.Decl):
            if isinstance(node.type, pycparser.c_ast.Struct):
                decls[node.type.name] = to_ctypes_struct(node.type.name, node.type, ctypes_pack)
            else:
                raise RuntimeError(node)
        elif isinstance(node, pycparser.c_ast.Pragma):
            args = node.string.split()
            if args[0] == "CTYPES_PACK":
                ctypes_pack = int(args[1]) if 1 < len(args) else 0
        else:
            raise RuntimeError(node)
    return decls


def main():
    with open("preprocessed.c", encoding="utf8") as file:
        data = file.read()

    parsed = get_decls(data)
    with open("mdl_structs.py", mode="w", encoding="utf8") as file:
        file.write('"""Auto-generated by c_struct_to_ctypes.py\n')
        file.write(
            "Reference:\n"
            + "1) https://github.com/ValveSoftware/source-sdk-2013/blob/0d8dceea4310fde5706b3ce1c70609d72a38efdf/sp/src/public/studio.h\n"
            + "2) https://github.com/ValveSoftware/source-sdk-2013/blob/0d8dceea4310fde5706b3ce1c70609d72a38efdf/sp/src/public/optimize.h\n"
        )
        file.write('"""\n')
        file.write("import ctypes\n")
        file.write("from gmod.custom_structure import PrintableStruct\n\n")

        for _, v in parsed.items():
            file.write(v + "\n\n\n")


if __name__ == "__main__":
    main()
