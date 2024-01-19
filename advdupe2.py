"""Reference: 
https://github.com/wiremod/advdupe2/blob/master/lua/advdupe2/sh_codec.lua"""

from lzma import decompress
from struct import unpack

class ReaderContextVersion4:
    def __init__(self, buff: bytes):
        self.buf = buff
        self.buf_index = 0
        self.reference = 0
        self.tables: dict[int, dict | list] = {}

    def decode(self, code: int):
        if code == 255:
            t = {}
            self.reference += 1
            ref = self.reference
            k = self.read()
            while k != '':
                r = self.read()
                t[k] = r
                k = self.read()
            self.tables[ref] = t
            return t

        if code == 254:
            l = []
            self.reference += 1
            ref = self.reference
            v = self.read()
            while v != '':
                l.append(v)
                v = self.read()
            self.tables[ref] = l
            return l

        if code == 253:
            return True

        if code == 252:
            return False

        if code == 251:
            double = unpack("<d", self.buf[self.buf_index:self.buf_index+8])[0]
            self.buf_index += 8
            return double

        if code == 250:
            vector = unpack("<ddd", self.buf[self.buf_index:self.buf_index+24])
            self.buf_index += 24
            return vector

        if code == 249:
            angle = unpack("<ddd", self.buf[self.buf_index:self.buf_index+24])
            self.buf_index += 24
            return angle

        if code == 248: # ascii, null terminated
            string = ""
            byte = self.read_bytes(1)[0]
            
            while byte != 0:
                string += chr(byte)
                byte = self.read_bytes(1)[0]

            return string

        if code == 247:
            self.reference += 1
            short = unpack("<h", self.buf[self.buf_index:self.buf_index+2])[0]
            self.buf_index += 2
            return self.tables[short]
        
        # maybe strings length < 247 (see v5)
        a = self.read_bytes(code).decode("ascii")
        return a

    def read(self) -> dict:
        code = self.buf[self.buf_index]
        self.buf_index += 1
        return self.decode(code)

    def read_bytes(self, length: int) -> bytes:
        self.buf_index += length
        return self.buf[self.buf_index-length: self.buf_index]

class ReaderContextVersion5:
    def __init__(self, buff: bytes):
        self.buf = buff
        self.buf_index = 0
        self.reference = 0
        self.tables: dict[int, dict | list] = {}

    def decode(self, code: int):
        if code == 255:
            t = {}
            self.reference += 1
            ref = self.reference
            k = self.read()
            while k != '' and k is not None:
                r = self.read()
                t[k] = r
                k = self.read()
            self.tables[ref] = t
            return t

        if code == 254:
            l = []
            self.reference += 1
            ref = self.reference
            v = self.read()
            while v != '' and v is not None:
                l.append(v)
                v = self.read()
            self.tables[ref] = l
            return l

        if code == 253:
            return True

        if code == 252:
            return False

        if code == 251:
            double = unpack("<d", self.buf[self.buf_index:self.buf_index+8])[0]
            self.buf_index += 8
            return double

        if code == 250:
            vector = unpack("<ddd", self.buf[self.buf_index:self.buf_index+24])
            self.buf_index += 24
            return vector

        if code == 249:
            angle = unpack("<ddd", self.buf[self.buf_index:self.buf_index+24])
            self.buf_index += 24
            return angle

        if code == 248: # Length>246 string
            length = unpack("<L", self.buf[self.buf_index:self.buf_index+4])[0]
            self.buf_index += 4
            string = self.read_bytes(length).decode("ascii")
            return string

        if code == 247:
            self.reference += 1
            short = unpack("<h", self.buf[self.buf_index:self.buf_index+2])[0]
            self.buf_index += 2
            return self.tables[short]
        
        if code == 246:
            return None

        if code == 0:
            return ""

        # ascii strings with length < 246
        a = self.read_bytes(code).decode("ascii")
        return a

    def read(self) -> dict:
        code = self.buf[self.buf_index]
        self.buf_index += 1
        return self.decode(code)

    def read_bytes(self, length: int) -> bytes:
        self.buf_index += length
        return self.buf[self.buf_index-length: self.buf_index]


def error_nodeserializer():
    raise RuntimeError("No deserializer")

class AdvDupe2:
    def __init__(self, dupe_path: str):
        self.dupe: dict
        with open(dupe_path, "rb") as file:
            self.dupe, self.info = self._decode(file.read())
        self._check_valid_dupe()

    def _get_info(self, dupe: bytes) -> tuple[dict, bytes]:
        last = dupe.find(b"\2")
        if last == -1:
            raise RuntimeError("Attempt to read AD2 file with malformed info block!")
        info = {}
        ss = dupe[:last]
        info_list = ss.split(b"\1")
        for i in range(len(info_list) // 2):
            info[info_list[i * 2]] = info_list[i * 2 + 1]

        if info[b"check"] != b"\r\n\t\n":
            if info[b"check"] == b"\x10\x09\x10":
                raise RuntimeError(
                    "Detected AD2 file corrupted in file transfer (newlines homogenized)(when using FTP, transfer AD2 files in image/binary mode, not ASCII/text mode)!"
                )
            raise RuntimeError("Attempt to read AD2 file with malformed info block!")

        return (info, dupe[last + 2 :])

    def _deserialize(self, reader_context: ReaderContextVersion4 | ReaderContextVersion5) -> dict:
        tbl = reader_context.read()
        return tbl

    def _decode_1(self, dupe) -> tuple[dict, dict]:
        raise NotImplementedError()

    def _decode_2(self, dupe) -> tuple[dict, dict]:
        raise NotImplementedError()

    def _decode_3(self, dupe) -> tuple[dict, dict]:
        raise NotImplementedError()

    def _decode_4(self, dupe: bytes) -> tuple[dict, dict]:
        info, dupestring = self._get_info(dupe[6:])
        return self._deserialize(ReaderContextVersion4(decompress(dupestring))), info

    def _decode_5(self, dupe) -> tuple[dict, dict]:
        info, dupestring = self._get_info(dupe[6:])
        return self._deserialize(ReaderContextVersion5(decompress(dupestring))), info

    def _decode(self, dupe: bytes) -> tuple[dict, dict]:
        max_supported_revision = 5
        sig = dupe[:4]
        rev = int(dupe[4])
        if sig != b"AD2F":
            if sig == b"[Inf":
                raise NotImplementedError("Adv.Dupe 1 not supported")
            raise RuntimeError("Corrupted file")
        if rev > max_supported_revision:
            raise RuntimeError("Version is not supported")
        if rev < 1:
            raise RuntimeError("Invalid revision")
        if rev == 1:
            return self._decode_1(dupe)
        if rev == 2:
            return self._decode_2(dupe)
        if rev == 3:
            return self._decode_3(dupe)
        if rev == 4:
            return self._decode_4(dupe)
        if rev == 5:
            return self._decode_5(dupe)
        
        raise RuntimeError("wtf")

    def _check_valid_dupe(self):
        errors: list[str] = []
        if not self.dupe['HeadEnt']:
            errors.append("Missing HeadEnt table")
        if not self.dupe['Entities']:
            errors.append("Missing Entities table")        
        if not self.dupe['Constraints']:
            errors.append("Missing Constraints table")   
        if not self.dupe['HeadEnt']['Z']:
            errors.append("Missing HeadEnt.Z table")   
        if not self.dupe['HeadEnt']['Pos']:
            errors.append("Missing HeadEnt.Pos")   
        if not self.dupe['HeadEnt']['Index']:
            errors.append("Missing HeadEnt.Index")   
        if not self.dupe['Entities'][self.dupe['HeadEnt']['Index']]:
            errors.append(f"Missing HeadEnt index {self.dupe['HeadEnt']['Index']} from Entities table")
        for key, data in self.dupe['Entities'].items():
            if 'PhysicsObjects' not in data:
                errors.append(f"Missing PhysicsObject table from Entity[{key}][{data['Class']}][{data['Model']}]")
            if not data['PhysicsObjects']:
                errors.append(f"Missing PhysicsObject[0] table from Entity['{key}'][{data['Class']}][{data['Model']}]")     
            if 'ad1' in self.info:
                raise RuntimeError("Adv Dupe 1 is not supported")
            if not data['PhysicsObjects'][0]['Pos']:
                errors.append(f"Missing PhysicsObject[0]['Pos'] table from Entity['{key}'][{data['Class']}][{data['Model']}]") 
            if not data['PhysicsObjects'][0]['Angle']:
                errors.append(f"Missing PhysicsObject[0]['Angle'] table from Entity['{key}'][{data['Class']}][{data['Model']}]") 
        return errors

# TODO: remove in release
def main():
    # "D:\Steam\steamapps\common\GarrysMod\garrysmod\data\advdupe2\test.txt"
    # "C:\Users\megaz\Desktop\volvo 940 diesel white.txt"
    dupe = AdvDupe2(r"D:\Steam\steamapps\common\GarrysMod\garrysmod\data\advdupe2\test.txt")
    print(dupe.dupe)

if __name__ == "__main__":
    main()
