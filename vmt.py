import pathlib
import warnings
import dataclasses
import enum

# class MaterialShader(enum.Enum):
#     UnlitGeneric = 1
#     VertexLitGeneric = 2

# @dataclasses.dataclass
# class Material:
#     material_shader: MaterialShader

class VMTParseError(RuntimeError):
    pass

class VMT:
    def __init__(self, path: str):
        self.path = path
        self.name = pathlib.Path(self.path).stem

        with open(path, encoding="utf-8") as file:
            data_raw = file.read()
        
        data_raw = data_raw.strip().strip("\"")

        self.shader_name: str = ""
        params_raw: str = ""

        for i in range(len(data_raw)):
            if data_raw[i:i+3] == "\"\n{":
                self.shader_name = data_raw[:i].lower()
                params_raw = data_raw[i+3:].strip("}").strip()
                break

            if data_raw[i:i+2] == "\"{":
                self.shader_name = data_raw[:i].lower()
                params_raw = data_raw[i+3:].strip("}").strip()
                break

            if data_raw[i:i+2] == "\n{":
                self.shader_name = data_raw[:i].lower()
                params_raw = data_raw[i+2:].strip("}").strip()
                break

        if not self.shader_name:
            raise VMTParseError(f"No shader name in {path}")

        self.params: dict[str, str] = {}

        for row in params_raw.split("\n"):
            row = row.strip()
            if row == "":
                continue
            args = [i.strip('"') for i in row.split()]
            # if no space between key and value
            if len(args) == 1:
                args = [i.strip('"') for i in row.split("\"\"")]
                
            if args[0].find("//") != -1:
                continue
            if len(args) != 2:
                args[1] = " ".join(args[1:])
                del args[2:]
            
            self.params[args[0].lower()] = args[1]
            



def main():
    vmt = VMT(r"C:\Users\megaz\Desktop\pizda\gmod_extract\sprops_new\materials\sprops\sprops_grid.vmt")
    print(vmt)

if __name__ == "__main__":
    main()