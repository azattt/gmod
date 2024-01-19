import ctypes

def print_array(array: ctypes.Array):
    TAB = " "*4
    print(array.__class__.__name__+"[")
    print(TAB+TAB.join((",\n".join(map(str, array))).splitlines(True)))
    print("]")

def read_until_null(bts: bytes) -> bytearray:
    byte = bytearray()
    for i in bts:
        if i == 0:
            break
        byte.append(i)
    return byte