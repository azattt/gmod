#pragma CTYPES_PACK 1
typedef unsigned char byte;
typedef struct
{
    float x;
    float y;
    float z;
} Vector;
struct studiohdr_t
{
    int id;
    int version;
    int checksum;
    char name[64];
    int dataLength;
    Vector eyeposition;
    Vector illumposition;
    Vector hull_min;
    Vector hull_max;
    Vector view_bbmin;
    Vector view_bbmax;
    int flags;
    int bone_count;
    int bone_offset;
    int bonecontroller_count;
    int bonecontroller_offset;
    int hitbox_count;
    int hitbox_offset;
    int localanim_count;
    int localanim_offset;
    int localseq_count;
    int localseq_offset;
    int activitylistversion;
    int eventsindexed;
    int texture_count;
    int texture_offset;
    int texturedir_count;
    int texturedir_offset;
    int skinreference_count;
    int skinrfamily_count;
    int skinreference_index;
    int bodypart_count;
    int bodypart_offset;
    int attachment_count;
    int attachment_offset;
    int localnode_count;
    int localnode_index;
    int localnode_name_index;
    int flexdesc_count;
    int flexdesc_index;
    int flexcontroller_count;
    int flexcontroller_index;
    int flexrules_count;
    int flexrules_index;
    int ikchain_count;
    int ikchain_index;
    int mouths_count;
    int mouths_index;
    int localposeparam_count;
    int localposeparam_index;
    int surfaceprop_index;
    int keyvalue_index;
    int keyvalue_count;
    int iklock_count;
    int iklock_index;
    float mass;
    int contents;
    int includemodel_count;
    int includemodel_index;
    int virtualModel;
    int animblocks_name_index;
    int animblocks_count;
    int animblocks_index;
    int animblockModel;
    int bonetablename_index;
    int vertex_base;
    int offset_base;
    byte directionaldotproduct;
    byte rootLod;
    byte numAllowedRootLods;
    byte unused0;
    int unused1;
    int flexcontrollerui_count;
    int flexcontrollerui_index;
    float vertAnimFixedPointScale;
    int unused2;
    int studiohdr2index;
    int unused3;
};
struct studiohdr2_t
{
    int srcbonetransform_count;
    int srcbonetransform_index;
    int illumpositionattachmentindex;
    float flMaxEyeDeflection;
    int linearbone_index;
    int unknown[64];
};
struct mstudiotexture_t
{
    int name_offset;
    int flags;
    int used;
    int unused;
    int material;
    int client_material;
    int unused2[10];
};

typedef struct
{
    const void *pVertexData;
    const void *pTangentData;
} mstudio_modelvertexdata_t;

typedef struct
{
    const mstudio_modelvertexdata_t *modelvertexdata;
    int numLODVertexes[8];
} mstudio_meshvertexdata_t;
struct mstudiomodel_t
{
    char name[64];

    int type;

    float boundingradius;

    int nummeshes;
    int meshindex;

    int numvertices;
    int vertexindex;
    int tangentsindex;

    int numattachments;
    int attachmentindex;

    int numeyeballs;
    int eyeballindex;

    mstudio_modelvertexdata_t vertexdata;

    int unused[8];
};
struct mstudiomesh_t
{
    int material;

    int modelindex;

    int numvertices;
    int vertexoffset;

    int numflexes;
    int flexindex;

    int materialtype;
    int materialparam;

    int meshid;

    Vector center;

    mstudio_meshvertexdata_t vertexdata;

    int unused[8];
};
struct mstudiohitboxset_t
{
    int sznameindex;
    int numhitboxes;
    int hitboxindex;
};
struct mstudiobodyparts_t
{
    int sznameindex;
    int nummodels;
    int base;
    int modelindex;
};
typedef struct
{
    float x, y, z, w;
} Quaternion;
typedef struct
{
    float x, y, z;
} RadianEuler;
typedef struct
{
    float m_flMatVal[12];
} matrix3x4_t;
struct mstudiobone_t
{
    int sznameindex;
    int parent;
    int bonecontroller[6];

    Vector pos;
    Quaternion quat;
    RadianEuler rot;

    Vector posscale;
    Vector rotscale;

    matrix3x4_t poseToBone;
    Quaternion qAlignment;
    int flags;
    int proctype;
    int procindex;
    int physicsbone;
    int surfacepropidx;
    int contents;

    int unused[8];
};
struct vertexFileHeader_t
{
    int id;
    int version;
    int checksum;
    int numLODs;
    int numLODVertexes[8];
    int numFixups;
    int fixupTableStart;
    int vertexDataStart;
    int tangentDataStart;
};
typedef struct
{
    float weight[3];
    char bone[3];
    byte numbones;
} mstudioboneweight_t;
typedef struct
{
    float x;
    float y;
} Vector2D;
struct mstudiovertex_t
{
    mstudioboneweight_t m_BoneWeights;
    Vector m_vecPosition;
    Vector m_vecNormal;
    Vector2D m_vecTexCoord;
};
struct FileHeader_t
{
    int version;
    int vertCacheSize;
    unsigned short maxBonesPerStrip;
    unsigned short maxBonesPerTri;
    int maxBonesPerVert;
    int checkSum;
    int numLODs;
    int materialReplacementListOffset;
    int numBodyParts;
    int bodyPartOffset;
};
struct BodyPartHeader_t
{
    int numModels;
    int modelOffset;
};
struct ModelHeader_t
{
    int numLODs;
    int lodOffset;
};
struct ModelLODHeader_t
{
    int numMeshes;
    int meshOffset;

    float switchPoint;
};
struct MeshHeader_t
{
    int numStripGroups;
    int stripGroupHeaderOffset;

    unsigned char flags;
};
struct StripGroupHeader_t
{
    int numVerts;
    int vertOffset;

    int numIndices;
    int indexOffset;

    int numStrips;
    int stripOffset;

    unsigned char flags;
};
struct StripHeader_t
{
    int numIndices;
    int indexOffset;

    int numVerts;
    int vertOffset;

    short numBones;

    unsigned char flags;

    int numBoneStateChanges;
    int boneStateChangeOffset;
};
struct Vertex_t
{
    unsigned char boneWeightIndex[3];
    unsigned char numBones;
    unsigned short origMeshVertID;
    char boneID[3];
};
struct mstudiobbox_t
{
    int bone;
    int group;
    Vector bbmin;
    Vector bbmax;
    int szhitboxnameindex;
    int unused[8];
};
struct mstudioanimdesc_t
{
    int baseptr;
    int sznameindex;
    float fps;
    int flags;
    int numframes;
    int nummovements;
    int movementindex;
    int unused1[6];
    int animblock;
    int animindex;
    int numikrules;
    int ikruleindex;
    int animblockikruleindex;
    int numlocalhierarchy;
    int localhierarchyindex;
    int sectionindex;
    int sectionframes;
    short zeroframespan;
    short zeroframecount;
    int zeroframeindex;
    float zeroframestalltime;
};
struct mstudioseqdesc_t
{
    int baseptr;
    int szlabelindex;
    int szactivitynameindex;
    int flags;
    int activity;
    int actweight;
    int numevents;
    int eventindex;
    Vector bbmin;
    Vector bbmax;
    int numblends;
    int animindexindex;
    int movementindex;
    int groupsize[2];
    int paramindex[2];
    float paramstart[2];
    float paramend[2];
    int paramparent;
    float fadeintime;
    float fadeouttime;
    int localentrynode;
    int localexitnode;
    int nodeflags;
    float entryphase;
    float exitphase;
    float lastframe;
    int nextseq;
    int pose;
    int numikrules;
    int numautolayers;
    int autolayerindex;
    int weightlistindex;
    int posekeyindex;
    int numiklocks;
    int iklockindex;
    int keyvalueindex;
    int keyvaluesize;
    int cycleposeindex;
    int unused[7];
};
struct MaterialReplacementHeader_t
{
    short materialID;
    int replacementMaterialNameOffset;
};

struct MaterialReplacementListHeader_t
{
    int numReplacements;
    int replacementOffset;
};
struct vertexFileFixup_t
{
    int lod;
    int sourceVertexID;
    int numVertexes;
};