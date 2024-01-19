import ctypes
import os
import struct
import time
import warnings
from pprint import pprint

from typing import Iterator, TypedDict

from gmod.misc import print_array, read_until_null
from gmod.mdl_structs import (
    studiohdr_t,
    studiohdr2_t,
    mstudiobone_t,
    mstudiobodyparts_t,
    mstudiomodel_t,
    mstudiomesh_t,
    vertexFileHeader_t,
    mstudiovertex_t,
    FileHeader_t,
    BodyPartHeader_t,
    ModelHeader_t,
    ModelLODHeader_t,
    MeshHeader_t,
    StripGroupHeader_t,
    StripHeader_t,
    Vertex_t,
    mstudiohitboxset_t,
    mstudiobbox_t,
    mstudioanimdesc_t,
    mstudioseqdesc_t,
    mstudiotexture_t,
    vertexFileFixup_t,
)

MODEL_VERTEX_FILE_ID = int.from_bytes(b"VSDI", "big")
MODEL_VERTEX_FILE_VERSION = 4
OPTIMIZED_MODEL_FILE_VERSION = 7


class SourceModel:
    def __init__(
        self,
        mdl_path,
        vtx_path: str | None = None,
        vvd_path: str | None = None,
        texture_path: str | None = None,
    ):
        self.mdl_header: studiohdr_t
        self.studiohdr2: studiohdr2_t
        self.vvd_header: vertexFileHeader_t
        self.vtx_header: FileHeader_t
        self.num_vertices: int
        self.num_indices: int

        # handling paths
        self.mdl_path = mdl_path
        if not vtx_path:
            vtx_extensions = [".dx90.vtx"]  # maybe add more?
            for ext in vtx_extensions:
                vtx_path = ".".join(self.mdl_path.split(".")[:-1]) + ext
                if os.path.exists(vtx_path):
                    self.vtx_path = vtx_path
                    break
            else:
                raise RuntimeError("Couldn't find .vtx file")
        else:
            self.vtx_path = vtx_path

        if not vvd_path:
            self.vvd_path = ".".join(self.mdl_path.split(".")[:-1]) + ".vvd"
            if not os.path.exists(self.vvd_path):
                raise RuntimeError("Couldn't find .vvd file")
        else:
            self.vvd_path = vvd_path

        self.texture_path = texture_path

        self.mdl_bytes = b""
        self.vtx_bytes = b""
        self.vvd_bytes = b""

        self.mdl_name: str
        self._check_files()

    def _check_files(self):
        with open(self.mdl_path, "rb") as mdl:
            mdl_id = int.from_bytes(mdl.read(4), "little")
            mdl_version = int.from_bytes(mdl.read(4), "little")
            mdl_checksum = int.from_bytes(mdl.read(4), "little")
            self.mdl_name = str(mdl.read(64), encoding="ascii")
        with open(self.vtx_path, "rb") as vtx:
            vtx_version = int.from_bytes(vtx.read(4), "little")
            vtx.seek(16, 0)
            vtx_checksum = int.from_bytes(vtx.read(4), "little")
        with open(self.vvd_path, "rb") as vvd:
            vvd_id = int.from_bytes(vvd.read(4), "little")
            vvd_version = int.from_bytes(vvd.read(4), "little")
            vvd_checksum = int.from_bytes(vvd.read(4), "little")

        if vvd_id != MODEL_VERTEX_FILE_ID:
            raise RuntimeError(
                f"Unknown magic number of VVD file {vvd_id}.\nShould be {MODEL_VERTEX_FILE_ID}"
            )
        if vvd_version != MODEL_VERTEX_FILE_VERSION:
            raise NotImplementedError(
                f"VVD version {vvd_version} not supported :(.\nSupported version is {MODEL_VERTEX_FILE_VERSION}"
            )
        if vvd_checksum != mdl_checksum:
            raise RuntimeError("VVD's checksum != MDL's checksum")
        if vtx_checksum != mdl_checksum:
            raise RuntimeError("VTX's checksum != MDL's checksum")

    def _load_mdl(self):
        if not self.mdl_bytes:
            with open(self.mdl_path, "rb") as file:
                self.mdl_bytes = file.read()
            self.mdl_header = studiohdr_t.from_buffer_copy(self.mdl_bytes)
            self.studiohdr2 = studiohdr2_t.from_buffer_copy(
                self.mdl_bytes, self.mdl_header.studiohdr2index
            )

    def _load_vtx(self):
        if not self.vtx_bytes:
            with open(self.vtx_path, "rb") as file:
                self.vtx_bytes = file.read()

    def _load_vvd(self):
        if not self.vvd_bytes:
            with open(self.vvd_path, "rb") as file:
                self.vvd_bytes = file.read()

    def _get_vertices(self) -> list[tuple]:
        self._load_vvd()
        self._load_mdl()
        self.vvd_header = vertexFileHeader_t.from_buffer_copy(self.vvd_bytes)
        fixups = (vertexFileFixup_t * self.vvd_header.numFixups).from_buffer_copy(
            self.vvd_bytes, self.vvd_header.fixupTableStart
        )
        start = self.vvd_header.vertexDataStart
        if self.vvd_header.numFixups != 0:
            start += fixups[0].sourceVertexID
            # print("numLODs", self.vvd_header.numLODs)
            # raise NotImplementedError("TODO: self.vvd_header.numLODs != 1")

        self.num_vertices = self.vvd_header.numLODVertexes[0]
        vertices = (mstudiovertex_t * self.num_vertices).from_buffer_copy(
            self.vvd_bytes, start
        )
        # print(vertices)
        vertices_list: list[tuple] = []

        for v in vertices:
            vertices_list.append(
                (
                    v.m_vecPosition.x,
                    v.m_vecPosition.y,
                    v.m_vecPosition.z,
                    v.m_vecNormal.x,
                    v.m_vecNormal.y,
                    v.m_vecNormal.z,
                    v.m_vecTexCoord.x,
                    v.m_vecTexCoord.y,
                )
            )

        return vertices_list

    def _get_indices(self) -> list[int]:
        self._load_vtx()

        self.vtx_header = FileHeader_t.from_buffer_copy(self.vtx_bytes)
        if self.vtx_header.numBodyParts != 1:
            print(f"self.vtx_header.numBodyParts: {self.vtx_header.numBodyParts}")
        if self.vtx_header.numLODs != 1:
            print(f"self.vtx_header.numLODs: {self.vtx_header.numLODs}")

        def get_offset(
            struct_type: type[ctypes.Structure], length: int, offset: int
        ) -> range:
            # pylint: disable=W0212
            return range(
                offset,
                offset + ctypes.sizeof(struct_type) * length,
                ctypes.sizeof(struct_type),
            )

        num_lods = self.vtx_header.numLODs
        strip_type = TypedDict("strip_type", {"hdr": StripHeader_t, "list": list})
        stripgroup_type = TypedDict(
            "stripgroup_type",
            {"hdr": StripGroupHeader_t, "offset": int, "strips": list[strip_type]},
        )
        mesh_type = TypedDict(
            "mesh_type", {"hdr": MeshHeader_t, "stripgroups": list[stripgroup_type]}
        )
        lod_type = TypedDict(
            "lod_type", {"hdr": ModelLODHeader_t, "meshes": list[mesh_type]}
        )
        model_type = TypedDict(
            "model_type", {"hdr": ModelHeader_t, "lods": list[lod_type]}
        )
        bodypart_type = TypedDict(
            "bodypart_type", {"hdr": BodyPartHeader_t, "models": list[model_type]}
        )
        bodyparts_name = self._get_bodypart()
        bodyparts: list[bodypart_type] = []
        for bodypart_offset in get_offset(
            BodyPartHeader_t,
            self.vtx_header.numBodyParts,
            self.vtx_header.bodyPartOffset,
        ):
            bodypart = BodyPartHeader_t.from_buffer_copy(
                self.vtx_bytes, bodypart_offset
            )
            bodyparts.append({"hdr": bodypart, "models": []})
            for modelheader_offset in get_offset(
                ModelHeader_t,
                bodypart.numModels,
                bodypart_offset + bodypart.modelOffset,
            ):
                modelheader = ModelHeader_t.from_buffer_copy(
                    self.vtx_bytes, modelheader_offset
                )
                bodyparts[-1]["models"].append({"hdr": modelheader, "lods": []})
                for modellodheader_offset in get_offset(
                    ModelLODHeader_t,
                    modelheader.numLODs,
                    modelheader_offset + modelheader.lodOffset,
                ):
                    modellodheader = ModelLODHeader_t.from_buffer_copy(
                        self.vtx_bytes, modellodheader_offset
                    )
                    bodyparts[-1]["models"][0]["lods"].append(
                        {"hdr": modellodheader, "meshes": []}
                    )
                    for meshheader_offset in get_offset(
                        MeshHeader_t,
                        modellodheader.numMeshes,
                        modellodheader_offset + modellodheader.meshOffset,
                    ):
                        meshheader = MeshHeader_t.from_buffer_copy(
                            self.vtx_bytes, meshheader_offset
                        )
                        bodyparts[-1]["models"][0]["lods"][0]["meshes"].append(
                            {"hdr": meshheader, "stripgroups": []}
                        )
                        for stripgroupheader_offset in get_offset(
                            StripGroupHeader_t,
                            meshheader.numStripGroups,
                            meshheader_offset + meshheader.stripGroupHeaderOffset,
                        ):
                            stripgroupheader = StripGroupHeader_t.from_buffer_copy(
                                self.vtx_bytes, stripgroupheader_offset
                            )
                            bodyparts[-1]["models"][0]["lods"][0]["meshes"][0][
                                "stripgroups"
                            ].append(
                                {
                                    "hdr": stripgroupheader,
                                    "strips": [],
                                    "offset": stripgroupheader_offset,
                                }
                            )
                            for stripheader_offset in get_offset(
                                StripHeader_t,
                                stripgroupheader.numStrips,
                                stripgroupheader_offset + stripgroupheader.stripOffset,
                            ):
                                stripheader = StripHeader_t.from_buffer_copy(
                                    self.vtx_bytes, stripheader_offset
                                )
                                bodyparts[-1]["models"][0]["lods"][0]["meshes"][0]["stripgroups"][
                                    0
                                ]["strips"].append({"hdr": stripheader, "list": []})


        last = bodyparts[0]["models"][0]["lods"][0]["meshes"][0]["stripgroups"][0]
        pprint(bodyparts[0]["models"][0]["lods"][0]["meshes"][0])
        offset = last["offset"]
        indices_unordered = (ctypes.c_ushort * last["hdr"].numIndices).from_buffer_copy(
            self.vtx_bytes, offset + last["hdr"].indexOffset
        )
        indices_mapping = [
            int.from_bytes(self.vtx_bytes[i + 4 : i + 6], "little")
            for i in range(
                offset + last["hdr"].vertOffset,
                offset + last["hdr"].vertOffset + 9 * last["hdr"].numVerts,
                9,
            )
        ]
        # print_array([Vertex_t.from_buffer_copy(self.vtx_bytes, i) for i in range(offset+last["hdr"].vertOffset, offset+last["hdr"].vertOffset+9*last["hdr"].numVerts, 9)])
        indices = [indices_mapping[i] for i in indices_unordered]
        # indices = indices_unordered
        return list(indices)
        # offset += modelheader.lodOffset
        # modellodheader = ModelLODHeader_t.from_buffer_copy(self.vtx_bytes, offset)
        # offset += modellodheader.meshOffset
        # meshheader = MeshHeader_t.from_buffer_copy(self.vtx_bytes, offset)
        # offset += meshheader.stripGroupHeaderOffset
        # stripgroupheader = StripGroupHeader_t.from_buffer_copy(self.vtx_bytes, offset)

        # num_indices: int = stripgroupheader.numIndices
        # indexoffset = offset + stripgroupheader.indexOffset
        # indices_arr = (ctypes.c_ushort * num_indices).from_buffer_copy(
        #     self.vtx_bytes, indexoffset
        # )

        # vertoffset = offset + stripgroupheader.vertOffset
        # num_vertices: int = stripgroupheader.numVerts
        # vertex_arr = (Vertex_t * num_vertices).from_buffer_copy(
        #     self.vtx_bytes, vertoffset
        # )

        # new_indices_arr = []
        # for i in indices_arr:
        #     new_indices_arr.append(vertex_arr[i].origMeshVertID)
        # return new_indices_arr

    def _get_bones(self) -> ctypes.Array[mstudiobone_t]:
        # flags here https://github.com/ValveSoftware/source-sdk-2013/blob/0d8dceea4310fde5706b3ce1c70609d72a38efdf/sp/src/public/studio.h#L373
        self._load_mdl()
        bone_count: int = self.mdl_header.bone_count
        bones = (mstudiobone_t * bone_count).from_buffer_copy(
            self.mdl_bytes, self.mdl_header.bone_offset
        )
        return bones

    def _get_hitboxes(self) -> ctypes.Array[mstudiohitboxset_t]:
        self._load_mdl()
        hitbox_count: int = self.mdl_header.hitbox_count
        hitboxes = (mstudiohitboxset_t * hitbox_count).from_buffer_copy(
            self.mdl_bytes, self.mdl_header.hitbox_offset
        )
        if hitbox_count != 1:
            raise NotImplementedError()
        if hitboxes[0].numhitboxes != 1:
            raise NotImplementedError()

        name = bytearray()
        for i in range(
            self.mdl_header.hitbox_offset + hitboxes[0].sznameindex,
            self.mdl_header.hitbox_offset + hitboxes[0].sznameindex + 64,
        ):
            if self.mdl_bytes[i] == 0:
                break
            name.append(self.mdl_bytes[i])

        offset = self.mdl_header.hitbox_offset + hitboxes[0].hitboxindex
        bbox = mstudiobbox_t.from_buffer_copy(self.mdl_bytes, offset)

        bbox_name = bytearray()
        for i in range(
            offset + bbox.szhitboxnameindex, offset + bbox.szhitboxnameindex + 64
        ):
            if self.mdl_bytes[i] == 0:
                break
            bbox_name.append(self.mdl_bytes[i])

        return hitboxes

    def _get_animation(self):
        self._load_mdl()
        animdesc = (
            mstudioanimdesc_t * self.mdl_header.localanim_count
        ).from_buffer_copy(self.mdl_bytes, self.mdl_header.localanim_offset)

    def _get_localsec(self):
        self._load_mdl()
        localsec = (mstudioseqdesc_t * self.mdl_header.localseq_count).from_buffer_copy(
            self.mdl_bytes, self.mdl_header.localseq_offset
        )

    def _get_textures(self) -> list[str]:
        self._load_mdl()

        tex_names: list[str] = []
        textures = (mstudiotexture_t * self.mdl_header.texture_count).from_buffer_copy(
            self.mdl_bytes, self.mdl_header.texture_offset
        )
        for i, tex in enumerate(textures):
            name_offset = (
                self.mdl_header.texture_offset
                + tex.name_offset
                + ctypes.sizeof(mstudiotexture_t) * i
            )
            tex_names.append(
                read_until_null(self.mdl_bytes[name_offset:]).decode("ascii")
            )

        texturedir_offset = list(
            self.mdl_bytes[
                self.mdl_header.texture_offset : self.mdl_header.texture_offset
                + self.mdl_header.texturedir_count
            ]
        )
        # for offset in texturedir_offset:
        #     print(read_until_null(self.mdl_bytes[offset:]))
        return tex_names

    def _get_skins(self):
        raise NotImplementedError()

    def _get_bodypart(self) -> list:
        self._load_mdl()

        model_type = TypedDict(
            "model_type", {"name": str, "meshes": ctypes.Array[MeshHeader_t]}
        )
        bodypart_type = TypedDict(
            "bodypart_type", {"name": str, "models": list[model_type]}
        )
        output: list[bodypart_type] = []

        bodypart_count: int = self.mdl_header.bodypart_count
        bodyparts = (mstudiobodyparts_t * bodypart_count).from_buffer_copy(
            self.mdl_bytes, self.mdl_header.bodypart_offset
        )

        for i, bodypart in enumerate(bodyparts):
            if bodypart.base != 1:
                warnings.warn("mstudiobodyparts_t.base != 1")
            bpart = {
                "name": read_until_null(
                    self.mdl_bytes[
                        self.mdl_header.bodypart_offset
                        + ctypes.sizeof(mstudiobodyparts_t) * i
                        + bodypart.sznameindex :
                    ]
                ),
                "models": [],
            }
            models_offset = (
                self.mdl_header.bodypart_offset
                + ctypes.sizeof(i * mstudiobodyparts_t)
                + bodypart.modelindex
            )
            models = (mstudiomodel_t * bodypart.nummodels).from_buffer_copy(
                self.mdl_bytes,
                models_offset,
            )

            for model in models:
                meshes = (mstudiomesh_t * model.nummeshes).from_buffer_copy(
                    self.mdl_bytes, models_offset + model.meshindex
                )
                models_offset += ctypes.sizeof(mstudiomodel_t)
                bpart["models"].append({"name": model.name, "meshes": meshes})

            output.append(bpart)
        return output

    def _get_material(self):
        self._load_mdl()
        # print(self.vtx_bytes[self.vtx_header.materialReplacementListOffset :])


def main():
    model = SourceModel(
        r"C:\Users\megaz\Desktop\pizda\gmod_extract\sprops_new\models\sprops\trans\train\double_36.mdl",
        texture_path=r"C:\Users\megaz\Desktop\pizda\gmod_extract\sprops_new\materials\sprops",
    )
    # model._get_bones()
    # model._get_hitboxes()
    # model._get_animation()
    # model._get_textures()
    # model._get_bodypart()
    model._get_indices()
    # model._get_material()


if __name__ == "__main__":
    main()
