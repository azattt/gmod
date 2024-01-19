import pathlib
import struct
import warnings
from enum import Enum



class ImageFormat(Enum):
    IMAGE_FORMAT_NONE = -1
    IMAGE_FORMAT_RGBA8888 = 0
    IMAGE_FORMAT_ABGR8888 = 1
    IMAGE_FORMAT_RGB888 = 2
    IMAGE_FORMAT_BGR888 = 3
    IMAGE_FORMAT_RGB565 = 4
    IMAGE_FORMAT_I8 = 5
    IMAGE_FORMAT_IA88 = 6
    IMAGE_FORMAT_P8 = 7
    IMAGE_FORMAT_A8 = 8
    IMAGE_FORMAT_RGB888_BLUESCREEN = 9
    IMAGE_FORMAT_BGR888_BLUESCREEN = 10
    IMAGE_FORMAT_ARGB8888 = 11
    IMAGE_FORMAT_BGRA8888 = 12
    IMAGE_FORMAT_DXT1 = 13
    IMAGE_FORMAT_DXT3 = 14
    IMAGE_FORMAT_DXT5 = 15
    IMAGE_FORMAT_BGRX8888 = 16
    IMAGE_FORMAT_BGR565 = 17
    IMAGE_FORMAT_BGRX5551 = 18
    IMAGE_FORMAT_BGRA4444 = 19
    IMAGE_FORMAT_DXT1_ONEBITALPHA = 19
    IMAGE_FORMAT_BGRA5551 = 20
    IMAGE_FORMAT_UV88 = 21
    IMAGE_FORMAT_UVWQ8888 = 22
    IMAGE_FORMAT_RGBA16161616F = 23
    IMAGE_FORMAT_RGBA16161616 = 24
    IMAGE_FORMAT_UVLX8888 = 25


class Tag:
    LOW_RES = b"\x01\x00\x00"
    HIGH_RES = b"\x30\x00\x00"
    ANIMATED_PARTICLE_SHEET = b"\x10\x00\x00"  # not supported
    CRC = b"CRC"
    LOD = b"LOD"
    FLAGS = b"TSO"
    KEY_VALUE = b"KVD"


FLAG_NO_DATA = 0x02


class VTF:
    def __init__(self, path: str | pathlib.Path, rel_path: str | pathlib.Path):
        with open(path, "rb") as data:
            self.data = data.read()

        self.rel_path = str(rel_path)
        self.version: tuple[int, int]
        self.width: int
        self.height: int
        self.flags: int
        self.frames: int
        self.firstFrame: int
        self.reflectivity: tuple[float, float, float]
        self.bumpmapScale: float
        self.highResImageFormat: int
        self.mipmapCount: int
        self.lowResImageFormat: int
        self.lowResImageWidth: int
        self.lowResImageHeight: int
        # version >= 7.0
        self.depth: int
        # version >= 7.3
        self.numResources: int

        self._lowRes_slice: slice = slice(0)
        self._highRes_slices: list[slice] = []

        self._parse()

    def _do_low_res(self, offset: int) -> int:
        if self.lowResImageFormat == ImageFormat.IMAGE_FORMAT_DXT1.value:
            compressed_size = (
                self.lowResImageWidth * self.lowResImageHeight // 2
            )  # because of fixed compression ratio
            self._lowRes_slice = slice(offset, offset + compressed_size)
        elif (
            self.lowResImageFormat
            == ImageFormat.IMAGE_FORMAT_DXT5.value
        ):
            compressed_size = (
                self.lowResImageWidth * self.lowResImageHeight // 4
            )
            self._lowRes_slice = slice(offset, offset + compressed_size)
        else:
            raise RuntimeError(
                "Format is not supported",
                ImageFormat(self.lowResImageFormat).name,
            )

        return offset + compressed_size
    
    def _do_high_res(self, offset: int):
        self._highRes_slices = [None] * self.mipmapCount
        if self.highResImageFormat == ImageFormat.IMAGE_FORMAT_DXT1.value:
            for i in range(self.mipmapCount):
                compressed_size = max(2 ** (2 * i - 1), 8)
                self._highRes_slices[i] = slice(offset, offset + compressed_size)
                offset += compressed_size
        elif (
            self.highResImageFormat
            == ImageFormat.IMAGE_FORMAT_DXT5.value
        ):
            for i in range(self.mipmapCount):
                width = height = max(2**i, 4)
                compressed_size = width * height
                self._highRes_slices[i] = slice(offset, offset + compressed_size)
                offset += compressed_size
        else:
            raise RuntimeError(
                "Format is not supported",
                ImageFormat(self.highResImageFormat).name,
            )

        return offset
    
    def _parse(self):
        fmt0 = "<4s2II"
        signature, version_major, version_minor, headerSize = struct.unpack(
            fmt0, self.data[: struct.calcsize(fmt0)]
        )
        if signature != b"VTF\0":
            raise RuntimeError("Invalid signature")

        self.version = (version_major, version_minor)
        if version_major != 7 or version_minor not in range(2, 7):
            raise RuntimeError("version error", version_major, version_minor)

        if headerSize < 80:
            raise RuntimeError("invalid header size", headerSize)

        offset = struct.calcsize(fmt0)
        fmt = "<HHIHH4x3f4xfIBIBBH"
        (
            self.width,
            self.height,
            self.flags,
            self.frames,
            self.firstFrame,
            reflectivity0,
            reflectivity1,
            reflectivity2,
            self.bumpmapScale,
            self.highResImageFormat,
            self.mipmapCount,
            self.lowResImageFormat,
            self.lowResImageWidth,
            self.lowResImageHeight,
            self.depth,
        ) = struct.unpack(fmt, self.data[offset : offset + struct.calcsize(fmt)])
        self.reflectivity = (reflectivity0, reflectivity1, reflectivity2)
        offset += struct.calcsize(fmt)
        
        if version_minor >= 3:
            fmt73 = "<3xI8x"
            self.numResources = struct.unpack(
                fmt73, self.data[offset : offset + struct.calcsize(fmt73)]
            )[0]
            offset += struct.calcsize(fmt73)

            # Resources
            fmt_resource = "<3sBI"
            for _ in range(self.numResources):
                tag, flags, offset = struct.unpack(
                    fmt_resource,
                    self.data[offset : offset + struct.calcsize(fmt_resource)],
                )
                if flags == FLAG_NO_DATA:
                    continue
                if flags == 0x00:
                    if tag == Tag.LOW_RES:
                        offset += self._do_low_res(offset)
                    elif tag == Tag.HIGH_RES:
                        offset += self._do_high_res(offset)
                    elif tag == Tag.LOD:
                        warnings.warn("Currently not supported LOD tag")
                    else:
                        warnings.warn("Unknown tag: " + str(tag))
                else:
                    raise RuntimeError("Unknown flag while parsing resources", flags)

                offset += struct.calcsize(fmt_resource)

        if version_minor < 3:
            # low res
            offset = headerSize
            offset = self._do_low_res(offset)
            offset = self._do_high_res(offset)
            if offset != len(self.data):
                raise RuntimeError(f"Didn't reach the end of file: {self.rel_path}. {offset} != {len(self.data)}")

    def get_low_res(self) -> tuple[bytes, int, int, int]:
        """Lazy-loading of low resolution image"""
        if self.lowResImageFormat == ImageFormat.IMAGE_FORMAT_DXT1.value:
            return self.data[self._lowRes_slice], self.lowResImageFormat, self.lowResImageWidth, self.lowResImageHeight
        if self.lowResImageFormat == ImageFormat.IMAGE_FORMAT_DXT5.value:
            return self.data[self._lowRes_slice], self.lowResImageFormat, self.lowResImageWidth, self.lowResImageHeight
        raise RuntimeError("somehow self.lowResImageFormat is not ImageFormat (didn't run _parse())")

    def get_high_res(self, mipmap_level: int) -> tuple[bytes, int, int, int]:
        """Lazy-loading of high resolution image"""
        inverted_mipmap_level = self.mipmapCount - mipmap_level - 1
        if mipmap_level > self.mipmapCount:
            raise IndexError("mipmap_level > self.mipmapCount")
        if self.highResImageFormat == ImageFormat.IMAGE_FORMAT_DXT1.value:
            width = height = 2**inverted_mipmap_level
            return self.data[self._highRes_slices[inverted_mipmap_level]], self.highResImageFormat, width, height
        if self.highResImageFormat == ImageFormat.IMAGE_FORMAT_DXT5.value:
            width = height = 2**inverted_mipmap_level
            return self.data[self._highRes_slices[inverted_mipmap_level]], self.highResImageFormat, max(2**inverted_mipmap_level, 4), max(2**inverted_mipmap_level, 4)

        raise RuntimeError("somehow self.highResImageFormat is not ImageFormat")


def main():
    # sprops_grid_12x12.vtf
    #
    path = r"C:\Users\megaz\Desktop\pizda\gmod_extract\sprops_new/materials\sprops\trans\misc\train_metal3.vtf"
    parsed = VTF(path, "")

    from PIL import Image

    image, num_channels, width, height = parsed.get_low_res()
    mode = ""
    if num_channels == 3:
        mode = "RGB"
    elif num_channels == 4:
        mode = "RGBA"
    im = Image.frombuffer(mode, (width, height), image)
    im.show()
    for i in range(parsed.mipmapCount):
        image, num_channels, width, height = parsed.get_high_res(i)      
        mode = ""
        if num_channels == 3:
            mode = "RGB"
        elif num_channels == 4:
            mode = "RGBA"
        im = Image.frombuffer(mode, (width, height), image)
        # im.save("xuy" + str(i) + ".png")
        im.show()


if __name__ == "__main__":
    main()
