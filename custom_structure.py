import ctypes


class matrix3x4_t(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("m_flMatVal", ctypes.c_float * 12)]


class PrintableStruct(ctypes.Structure):
    def __str__(self) -> str:
        output = f"struct {self.__class__.__name__}" + "{\n"
        # pylint: disable-next=protected-access
        TAB = " " * 4
        for field in self._fields_:
            data = getattr(self, field[0])
            if isinstance(data, ctypes.Array):
                output += TAB + field[0] + " = " + data.__class__.__name__ + "[\n"
                output += (
                    TAB * 2
                    + (TAB * 2).join((",\n".join(map(str, data))).splitlines(True))
                    + "\n"
                )
                output += TAB + "]\n"
            # elif isinstance(data, matrix3x4_t):
            #     output += "matrix3x4_t{\n"
            #     for i in range(3):
            #         for j in range(4):
            #             output += str(data.m_flMatVal[i * 3 + j]) + "\n"
            #     output += "}\n"
            elif isinstance(data, ctypes.Structure):
                output += TAB + TAB.join(str(data).splitlines(True)) + "\n"
            else:
                output += TAB + field[0] + " = " + str(data) + "\n"
        output += "}"
        return output


def test():
    from misc import print_array

    class AnotherStruct(PrintableStruct):
        _fields_ = (("xuy", ctypes.c_int), ("piska", ctypes.c_char * 5))

    class Test(PrintableStruct):
        _fields_ = (("hello", AnotherStruct * 4), ("world", ctypes.c_char * 5))

    arr = (Test * 5)()
    print_array(arr)
    # print(AnotherStruct())


if __name__ == "__main__":
    test()
