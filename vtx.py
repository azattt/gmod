import os
import struct
import warnings


def main():
    path = r"C:\Users\megaz\Desktop\pizda\gmod_extract\sprops_new\models\sprops\rectangles\size_6\rect_96x108x3.mdl"
    content = b""
    with open(path, "rb") as file:
        content = file.read()
    header_format = "<iiHHiiiiii"
    (
        version,
        vertCacheSize,
        maxBonesPerStrip,
        maxBonesPerTri,
        maxBonesPerVert,
        checkSum,
        numLODs,
        materialReplacementListOffset,
        numBodyParts,
        bodyPartOffset,
    ) = struct.unpack(header_format, content[: struct.calcsize(header_format)])

    # Body array
    format = "ii"
    offset = bodyPartOffset
    for _ in range(numBodyParts):
        numModels, modelOffset = struct.unpack(
            format, content[offset : offset + struct.calcsize(format)]
        )
        offset += struct.calcsize(format)

    # Model array
    format = "ii"
    offset = bodyPartOffset
    for _ in range(numBodyParts):
        numLODs, lodOffset = struct.unpack(
            format, content[offset : offset + struct.calcsize(format)]
        )
        offset += struct.calcsize(format)
    # LOD Mesh array
    format = "iif"
    offset = bodyPartOffset
    for _ in range(numBodyParts):
        numMeshes, meshOffset, switchPoint = struct.unpack(
            format, content[offset : offset + struct.calcsize(format)]
        )
        offset += struct.calcsize(format)
    # Strip Group Array
    format = "iiiiiiBii"
    offset = bodyPartOffset
    for _ in range(numBodyParts):
        (
            numVerts,
            vertOffset,
            numIndices,
            indexOffset,
            numStrips,
            stripOffset,
            flags,
            numTopologyIndices,
            topologyOffset,
        ) = struct.unpack(format, content[offset : offset + struct.calcsize(format)])
        offset += struct.calcsize(format)


if __name__ == "__main__":
    main()
