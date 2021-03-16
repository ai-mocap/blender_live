import bpy
from mathutils import Quaternion

import os.path
import pathlib


mpii_joints = [
    "root",

    "thumb1",
    "thumb2",
    "thumb3",
    "thumb4",

    "index1",
    "index2",
    "index3",
    "index4",

    "middle1",
    "middle2",
    "middle3",
    "middle4",

    "ring1",
    "ring2",
    "ring3",
    "ring4",

    "pinky1",
    "pinky2",
    "pinky3",
    "pinky4",
]

mpii_parents = dict(
    root=None,

    thumb1='root',
    thumb2='thumb1',
    thumb3='thumb2',
    thumb4='thumb3',

    index1='root',
    index2='index1',
    index3='index2',
    index4='index3',

    middle1='root',
    middle2='middle1',
    middle3='middle2',
    middle4='middle3',

    ring1='root',
    ring2='ring1',
    ring3='ring2',
    ring4='ring3',

    pinky1='root',
    pinky2='pinky1',
    pinky3='pinky2',
    pinky4='pinky3',
)


def create_hands():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    if not bpy.context.scene.objects.get("left_Skeleton"):
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete()

        for ob in bpy.data.objects:
            if ob.type == "CAMERA":
                ob.select_set(False)

        left = Hand('left_')
        left.create_bones()
        right = Hand('right_')
        right.create_bones()
        return left, right


def load_hands():
    filepath = pathlib.Path(os.path.dirname(__file__)).parent.resolve() / "resources" / "handlmoved.blend"

    with bpy.data.libraries.load(str(filepath)) as (data_from, data_to):
        data_to.objects = data_from.objects

    objects = bpy.context.view_layer.active_layer_collection.collection.objects
    for obj in data_to.objects:
        if obj is not None:
            objects.link(obj)


class Hand:
    def __init__(self, prefix):
        self.prefix = prefix
        self.ref_quats = {None: Quaternion()}
        self.ref_scales = {None: 1.}
        self.enable_scale = False

    @property
    def object(self):
        name = self.prefix + "Skeleton"
        if name in bpy.data.objects:
            return bpy.data.objects[name]

    def reset_pose(self):
        if self.object is None:
            return
        for bone in self.object.pose.bones:
            bone.rotation_quaternion = Quaternion()

    def save_pose(self):
        if self.object is None:
            return
        self.object.select_set(True)
        bpy.context.view_layer.objects.active = self.object
        bpy.ops.object.mode_set(mode="EDIT", toggle=False)
        edit_bones = self.object.data.edit_bones
        for joint in mpii_joints:
            if joint in edit_bones:
                self.ref_quats[joint] = edit_bones[joint].matrix.to_quaternion()
                self.ref_scales[joint] = edit_bones[joint].length
            else:
                self.ref_quats[joint] = self.ref_quats[mpii_parents[joint]]
                self.ref_scales[joint] = self.ref_scales[mpii_parents[joint]]

    def process_bones(self, relative_rotations, relative_scales):
        for idx, bone in enumerate(mpii_joints):
            parent = mpii_parents[bone]
            rel_quat = relative_rotations[idx]
            rel_scale = relative_scales[idx - 1] if idx else 1.

            bones = self.object.pose.bones
            if bone in bones:
                obj = bones[bone]
                obj.rotation_mode = "QUATERNION"
                obj.rotation_quaternion = self.ref_quats[bone].inverted() @ self.ref_quats[parent] @ Quaternion(rel_quat)
                scale = rel_scale * self.ref_scales[parent] / self.ref_scales[bone] if self.enable_scale else 1
                obj.scale = (scale, scale, scale)
                if bpy.context.scene.cptr_recording:
                    obj.keyframe_insert(data_path="rotation_quaternion", index=-1)
